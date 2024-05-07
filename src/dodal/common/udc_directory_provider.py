from pathlib import Path

from ophyd_async.core import DirectoryInfo

from dodal.common.types import UpdatingDirectoryProvider


class UDCDirectoryProvider(UpdatingDirectoryProvider):
    resource_dir = Path("panda")

    def __init__(self, directory: Path | None = None):
        self._directory_info = (
            DirectoryInfo(root=directory, resource_dir=self.resource_dir)
            if directory
            else None
        )

    def update(self, directory: Path):
        self._directory_info = DirectoryInfo(
            root=directory, resource_dir=self.resource_dir
        )

    def __call__(self) -> DirectoryInfo:
        return self._directory_info
