"""Secure validation and local storage for uploaded videos."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov"}
ALLOWED_CONTENT_TYPES = {
    ".mp4": {"video/mp4"},
    ".avi": {"video/x-msvideo", "video/avi"},
    ".mov": {"video/quicktime"},
}
CHUNK_SIZE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class StoredVideo:
    """Metadata describing a successfully stored upload."""

    id: str
    original_filename: str
    stored_filename: str
    content_type: str
    size_bytes: int
    path: Path


class VideoStorageService:
    """Stream validated uploads to local disk without trusting client filenames."""

    def __init__(self) -> None:
        self._owners: dict[str, str] = {}

    async def store(self, upload: UploadFile, owner_id: str) -> StoredVideo:
        """Validate and store one upload, deleting partial files after any failure."""

        original_filename = Path(upload.filename or "").name
        extension = Path(original_filename).suffix.lower()
        self._validate_extension(extension)

        content_type = (upload.content_type or "").lower()
        self._validate_content_type(extension, content_type)

        settings = get_settings()
        upload_directory = settings.storage_root / "uploads"
        upload_directory.mkdir(parents=True, exist_ok=True)

        video_id = str(uuid4())
        stored_filename = f"{video_id}{extension}"
        final_path = upload_directory / stored_filename
        temporary_path = upload_directory / f"{video_id}.part"
        maximum_bytes = settings.max_upload_size_mb * 1024 * 1024
        size_bytes = 0
        header = b""

        try:
            with temporary_path.open("xb") as destination:
                while chunk := await upload.read(CHUNK_SIZE_BYTES):
                    size_bytes += len(chunk)
                    if size_bytes > maximum_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=(
                                f"Video exceeds the {settings.max_upload_size_mb} MB upload limit."
                            ),
                        )
                    if len(header) < 12:
                        header = (header + chunk)[:12]
                    destination.write(chunk)

            if size_bytes == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The uploaded video is empty.",
                )
            self._validate_file_signature(extension, header)
            temporary_path.replace(final_path)
            self._owners[video_id] = owner_id
        except Exception:
            temporary_path.unlink(missing_ok=True)
            final_path.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()

        return StoredVideo(
            id=video_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            path=final_path,
        )

    def require_owner(self, video_id: str, owner_id: str) -> str:
        """Hide temporary uploads from every account except their creator."""

        try:
            safe_id = str(UUID(video_id))
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video ID must be a valid UUID.",
            ) from error
        if self._owners.get(safe_id) != owner_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")
        return safe_id

    def release(self, video_id: str, owner_id: str) -> None:
        """Delete an owner's temporary upload and processed server output."""

        safe_id = self.require_owner(video_id, owner_id)
        storage_root = get_settings().storage_root
        for upload_path in (storage_root / "uploads").glob(f"{safe_id}.*"):
            upload_path.unlink(missing_ok=True)
        (storage_root / "processed" / f"{safe_id}.mp4").unlink(missing_ok=True)
        (storage_root / "processed" / f"{safe_id}.opencv.mp4").unlink(missing_ok=True)
        (storage_root / "processed" / f"{safe_id}.part.mp4").unlink(missing_ok=True)
        self._owners.pop(safe_id, None)

    def cleanup_stale(self, retention_hours: float = 24.0) -> int:
        """Remove abandoned temporary video files left by closed browsers or restarts."""

        cutoff = datetime.now(UTC) - timedelta(hours=retention_hours)
        deleted = 0
        storage_root = get_settings().storage_root
        for directory_name in ("uploads", "processed"):
            directory = storage_root / directory_name
            if not directory.is_dir():
                continue
            for path in directory.iterdir():
                if not path.is_file():
                    continue
                modified = datetime.fromtimestamp(path.stat().st_mtime, UTC)
                if modified < cutoff:
                    path.unlink(missing_ok=True)
                    deleted += 1
        return deleted

    @staticmethod
    def _validate_extension(extension: str) -> None:
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported extension. Upload an MP4, AVI, or MOV video.",
            )

    @staticmethod
    def _validate_content_type(extension: str, content_type: str) -> None:
        if content_type not in ALLOWED_CONTENT_TYPES[extension]:
            expected_types = ", ".join(sorted(ALLOWED_CONTENT_TYPES[extension]))
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Invalid MIME type for {extension}: expected {expected_types}.",
            )

    @staticmethod
    def _validate_file_signature(extension: str, header: bytes) -> None:
        """Reject renamed non-video files using standard container signatures."""

        is_iso_media = len(header) >= 12 and header[4:8] == b"ftyp"
        is_avi = len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"AVI "
        signature_is_valid = is_avi if extension == ".avi" else is_iso_media
        if not signature_is_valid:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="File contents do not match the selected video format.",
            )


video_storage_service = VideoStorageService()
