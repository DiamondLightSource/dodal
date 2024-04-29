from pathlib import Path

from ophyd_async.core import DirectoryInfo

_directory_info: DirectoryInfo


def set_directory(directory: Path):
    """
    Set the current base directory of the UDC DirectoryProvider.
    Files will be stored in the 'panda' subdirectory.
    """
    global _directory_info
    _directory_info = DirectoryInfo(
        root=directory, resource_dir=Path("panda"), prefix="", suffix=""
    )


def get_udc_directory_provider():
    """Get the singleton instance of the UDC DirectoryProvider"""
    return _get_directory


def _get_directory() -> DirectoryInfo:
    return _directory_info
