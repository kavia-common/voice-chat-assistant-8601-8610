import os
import tempfile
from typing import Tuple, Optional


def _guess_extension_from_mime(mime: Optional[str]) -> str:
    """Return a safe file extension based on MIME type."""
    mapping = {
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
    }
    return mapping.get(mime or "", ".bin")


# PUBLIC_INTERFACE
def save_uploaded_file_temporarily(file_obj) -> Tuple[str, str]:
    """Save uploaded InMemoryUploadedFile/TemporaryUploadedFile to a temp path.

    Returns:
        (path, extension): Absolute file path and guessed extension for the file.
    """
    ext = _guess_extension_from_mime(getattr(file_obj, "content_type", None))
    fd, path = tempfile.mkstemp(prefix="audio_", suffix=ext)
    with os.fdopen(fd, "wb") as tmp:
        for chunk in file_obj.chunks():
            tmp.write(chunk)
    return path, ext


# PUBLIC_INTERFACE
def safe_unlink(path: Optional[str]) -> None:
    """Safely delete a file path if it exists."""
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        # Best-effort cleanup; ignore errors
        pass
