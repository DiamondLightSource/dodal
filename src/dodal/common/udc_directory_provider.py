import os
from pathlib import Path

from ophyd_async.core import DirectoryInfo

from dodal.common.types import UpdatingDirectoryProvider
from dodal.log import LOGGER


class PandASubdirectoryProvider(UpdatingDirectoryProvider):
    """Directory provider for the HDFPanda. Points to, and optionally creates, a panda subdirectory relative to the
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

    def update(self, directory: Path, create_directory=False):
        if create_directory:
            panda_directory = f"{directory}/{self.resource_dir}"
            # At some point in the future, ophyd_async will have the feature to create the requested directory
            if not os.path.isdir(panda_directory):
                LOGGER.debug(f"Creating PandA PCAP subdirectory at {panda_directory}")
                os.makedirs(panda_directory)
        self._directory_info = DirectoryInfo(
            root=directory, resource_dir=self.resource_dir
        )

    def __call__(self) -> DirectoryInfo:
        if self._directory_info is None:
            raise ValueError(
                "Directory unknown for PandA to write into, update() needs to be called at least once"
            )
        return self._directory_info
