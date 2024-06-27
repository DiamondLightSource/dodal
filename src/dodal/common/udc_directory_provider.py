from pathlib import Path

from ophyd_async.core import DirectoryInfo

from dodal.common.types import UpdatingDirectoryProvider
from dodal.log import LOGGER


class PandASubdirectoryProvider(UpdatingDirectoryProvider):
    """Directory provider for the HDFPanda. Points to a panda subdirectory within the
    directory path provided, which must exist before attempting to arm the PCAP block"""

    resource_dir = Path("panda")

    def __init__(self, directory: Path | None = None):
        if directory is None:
            LOGGER.debug(
                f"{self.__class__.__name__} instantiated with no root path, update() must be called before writing data!"
            )
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
        if self._directory_info is None:
            raise ValueError(
                "Directory unknown for PandA to write into, update() needs to be called at least once"
            )
        return self._directory_info
