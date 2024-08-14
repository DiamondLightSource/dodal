from pathlib import Path

from ophyd_async.core import DirectoryInfo

from dodal.common.types import UpdatingDirectoryProvider
from dodal.log import LOGGER


class PandASubdirectoryProvider(UpdatingDirectoryProvider):
    """Directory provider for the HDFPanda. Points to a panda subdirectory within the
    directory path provided"""

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

    async def update(self, *, directory: Path, suffix: str = "", **kwargs):
        """Update the root directory into which panda pcap files are written. This will result in the panda
        subdirectory being created if it does not already exist.
         Args:
             directory: Path instance that identifies the root folder. This folder must exist. The panda will
                attempt to write into the "panda" subdirectory which will be created if not already present.
             suffix: Optional str that will be appended to the panda device name along with the file
                type extension to construct the output filename
        """
        output_directory = directory / self.resource_dir
        output_directory.mkdir(exist_ok=True)

        self._directory_info = DirectoryInfo(
            root=directory, resource_dir=self.resource_dir, suffix=suffix
        )

    def __call__(self) -> DirectoryInfo:
        if self._directory_info is None:
            raise ValueError(
                "Directory unknown for PandA to write into, update() needs to be called at least once"
            )
        return self._directory_info
