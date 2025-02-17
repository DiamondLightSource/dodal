from pathlib import Path

from ophyd_async.core import FilenameProvider, PathInfo

from dodal.common.types import UpdatingPathProvider
from dodal.log import LOGGER


class PandAFilenameProvider(FilenameProvider):
    def __init__(self, suffix: str | None = None):
        self.suffix = suffix

    def __call__(self, device_name: str | None = None):
        return f"{device_name}-{self.suffix}"


class PandASubpathProvider(UpdatingPathProvider):
    """Directory provider for the HDFPanda. Points to a panda subdirectory within the
    directory path provided"""

    resource_dir = Path("panda")

    def __init__(self, root_directory: Path | None = None, suffix: str = ""):
        self._output_directory: Path | None = (
            root_directory / self.resource_dir if root_directory else None
        )
        self._filename_provider = PandAFilenameProvider(suffix=suffix)
        if self._output_directory is None:
            LOGGER.debug(
                f"{self.__class__.__name__} instantiated with no root path, update() must be called before writing data!"
            )

    async def data_session(self) -> str:
        return self._filename_provider.suffix or ""

    async def update(self, *, directory: Path, suffix: str = "", **kwargs):
        """Update the root directory into which panda pcap files are written. This will result in the panda
        subdirectory being created if it does not already exist.
         Args:
             directory: Path instance that identifies the root folder. This folder must exist. The panda will
                attempt to write into the "panda" subdirectory which will be created if not already present.
             suffix: Optional str that will be appended to the panda device name along with the file
                type extension to construct the output filename
        """
        self._output_directory = directory / self.resource_dir
        self._filename_provider.suffix = suffix

    def __call__(self, device_name: str | None = None) -> PathInfo:
        assert self._output_directory, (
            "Directory unknown for PandA to write into, update() needs to be called at least once"
        )
        return PathInfo(
            directory_path=self._output_directory,
            filename=self._filename_provider(device_name),
            create_dir_depth=-1,  # allows PandA HDFWriter to make any number of dirs
        )
