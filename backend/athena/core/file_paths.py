from pathlib import Path
from urllib.parse import unquote


def resolve_data_file_path(raw_path: str | None, data_dir: Path) -> Path | None:
    """Verilen path'i data_dir altindaki gercek dosya yoluna cozer.

    Desteklenen formatlar:
    - relative: "102/file.pdf"
    - legacy absolute: "/data/library/102/file.pdf"
    - legacy non-slash: "data/library/102/file.pdf"
    """
    raw = unquote((raw_path or "").strip())
    if not raw:
        return None

    normalized = raw.replace("\\", "/")
    candidates: list[str] = [normalized]

    if normalized.startswith("/data/library/"):
        candidates.append(normalized[len("/data/library/"):])
    if normalized.startswith("data/library/"):
        candidates.append(normalized[len("data/library/"):])
    if normalized.startswith("/"):
        candidates.append(normalized.lstrip("/"))

    root = data_dir.resolve()
    for candidate in candidates:
        candidate = candidate.strip("/")
        if not candidate:
            continue
        resolved = (root / candidate).resolve()
        if not resolved.is_relative_to(root):
            continue
        if resolved.is_file():
            return resolved

    # Son sans: mutlak path verilmis olabilir
    try:
        absolute = Path(normalized).resolve()
        if absolute.is_relative_to(root) and absolute.is_file():
            return absolute
    except Exception:
        return None

    return None


def to_relative_data_path(file_path: Path, data_dir: Path) -> str:
    """Data dir altindaki dosya yolunu relative string'e cevirir."""
    try:
        return str(file_path.resolve().relative_to(data_dir.resolve()))
    except Exception:
        return str(file_path)
