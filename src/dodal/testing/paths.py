from pathlib import Path


def is_path_banned(path: Path, banned_paths: list[Path]) -> bool:
    resolved = path.resolve()
    return resolved.is_absolute() and any(
        resolved.is_relative_to(banned) for banned in banned_paths
    )
