"""Convert OpenCV output into browser-compatible H.264 MP4 video."""

import subprocess
from pathlib import Path

import imageio_ffmpeg


class MediaEncodingService:
    """Use the bundled FFmpeg binary to create Chrome-compatible video."""

    def convert_to_browser_mp4(self, source: Path, destination: Path) -> None:
        """Encode H.264 video with a widely supported pixel format."""

        destination.unlink(missing_ok=True)
        command = [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-i",
            str(source),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(destination),
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0 or not destination.is_file():
            destination.unlink(missing_ok=True)
            error_detail = completed.stderr.strip().splitlines()
            final_error = error_detail[-1] if error_detail else "Unknown FFmpeg error."
            raise RuntimeError(f"Could not create browser-compatible video: {final_error}")


media_encoding_service = MediaEncodingService()
