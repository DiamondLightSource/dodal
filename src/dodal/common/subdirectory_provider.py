from pathlib import Path

from ophyd_async.core import FilenameProvider, PathInfo

from dodal.common.types import UpdatingPathProvider
from dodal.log import LOGGER


class CustomFilenameProvider(FilenameProvider):
    def __init__(self, beamline: str, prefix: str | None = None) -> None:
        self.prefix = prefix
        self._beamline = beamline

    def __call__(self, device_name: str | None = None) -> str:
        if self.prefix:
            return self.prefix
        else:
            return f"{self._beamline}-{device_name}"


class SubdirectoryPathProvider(UpdatingPathProvider):
    def __init__(
        self,
        beamline: str,
        visit_directory: Path | None = None,
        subdirectory: str = "",
        prefix: str = "",
    ) -> None:
        self._beamline = beamline
        self._output_directory: Path | None = (
            visit_directory / subdirectory if visit_directory else None
        )
        self._filename_provider = CustomFilenameProvider(
            beamline=self._beamline, prefix=prefix
        )
        if self._output_directory is None:
            LOGGER.debug(
                f"""{self.__class__.__name__} instantiated with no root path,
                update() must be called before writing data!"""
            )

    def __call__(self, device_name: str | None = None) -> PathInfo:
        assert self._output_directory, (
            "Directory unknown, update() must be called at least once"
        )
        return PathInfo(
            directory_path=self._output_directory,
            filename=self._filename_provider(device_name),
        )

    async def data_session(self) -> str:
        return self._filename_provider.prefix or ""

    async def update(
        self, *, directory: Path, subdirectory: str, prefix: str = "", **kwargs
    ):
        """Update the directory into which the files are written, as well as the
        filename if a custom one is passed.

        Args:
            directory (Path): Instance that identifies the root folder, usually the
            visit directory.
            subdirectory (str): Name of the subdirectory in which we want the files to
            end up. This directory must already exist upon calling update.
            prefix(str, optional): Custom filename for the output. If not passed it will
            default to {beamline}-{device_name}.
            **kwargs: Any additional arguments. Unused in this case.
        """
        self._output_directory = directory / subdirectory
        self._filename_provider.prefix = prefix
