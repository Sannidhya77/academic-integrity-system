from pathlib import Path

from werkzeug.utils import secure_filename


def submission_disk_path(upload_root: Path, submission_id: int, filename: str) -> Path:
    safe = secure_filename(filename) or "unnamed"
    return upload_root / f"{submission_id}_{safe}"


def try_save_upload(
    upload_root: Path,
    submission_id: int,
    filename: str,
    content: str,
    enabled: bool,
) -> None:
    if not enabled:
        return
    upload_root.mkdir(parents=True, exist_ok=True)
    path = submission_disk_path(upload_root, submission_id, filename)
    path.write_text(content, encoding="utf-8")
