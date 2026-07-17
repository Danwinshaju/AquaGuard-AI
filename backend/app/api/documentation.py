"""Downloadable operator and demonstration documentation."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.core.config import PROJECT_DIRECTORY

router = APIRouter()

GUIDES = {
    "user-guide": "USER-GUIDE.md",
    "accounts-and-storage-guide": "ACCOUNTS-AND-STORAGE-GUIDE.md",
    "live-demo-guide": "LIVE-DEMO-GUIDE.md",
    "troubleshooting-guide": "TROUBLESHOOTING-GUIDE.md",
    "aquatic-model-training": "AQUATIC-MODEL-TRAINING.md",
}


@router.get("/{guide_name}", response_class=FileResponse)
async def download_guide(guide_name: str) -> FileResponse:
    """Return one allowlisted guide without exposing arbitrary local files."""

    filename = GUIDES.get(guide_name)
    if filename is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documentation guide not found.",
        )
    path = PROJECT_DIRECTORY / "docs" / filename
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documentation file is missing.",
        )
    return FileResponse(path, media_type="text/markdown", filename=filename)
