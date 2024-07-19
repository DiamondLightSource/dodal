from pathlib import Path

import aiofiles
from aiohttp import ClientSession
from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_rw

from dodal.log import LOGGER


class Webcam(StandardReadable, Triggerable):
    def __init__(self, name, prefix, url):
        self.url = url
        self.filename = soft_signal_rw(str, name="filename")
        self.directory = soft_signal_rw(str, name="directory")
        self.last_saved_path = soft_signal_rw(str, name="last_saved_path")

        self.set_readable_signals([self.last_saved_path])
        super().__init__(name=name)

    async def _write_image(self, file_path: str):
        async with ClientSession() as session:
            async with session.get(self.url) as response:
                response.raise_for_status()
                LOGGER.info(f"Saving webcam image from {self.url} to {file_path}")
                async with aiofiles.open(file_path, "wb") as file:
                    await file.write((await response.read()))

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        filename = await self.filename.get_value()
        directory = await self.directory.get_value()

        file_path = Path(f"{directory}/{filename}.png").as_posix()
        await self._write_image(file_path)
        await self.last_saved_path.set(file_path)
