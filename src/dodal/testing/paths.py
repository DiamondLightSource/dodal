from pathlib import Path

BANNED_PATHS = [Path("/dls"), Path("/dls_sw")]


def is_path_banned(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path
    return resolved.is_absolute() and any(
        resolved.is_relative_to(banned) for banned in BANNED_PATHS
    )
