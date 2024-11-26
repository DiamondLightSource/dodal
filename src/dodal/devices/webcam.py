from collections.abc import ByteString
from io import BytesIO
from pathlib import Path

import aiofiles
from aiohttp import ClientSession
from bluesky.protocols import Triggerable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_rw,
)
from PIL import Image

from dodal.log import LOGGER

PLACEHOLDER_IMAGE_SIZE = (1024, 768)
IMAGE_FORMAT = "png"


def create_placeholder_image() -> ByteString:
    image = Image.new("RGB", PLACEHOLDER_IMAGE_SIZE)
    image.save(buffer := BytesIO(), format=IMAGE_FORMAT)
    return buffer.getbuffer()


class Webcam(StandardReadable, Triggerable):
    def __init__(self, name, prefix, url):
        self.url = url
        self.filename = soft_signal_rw(str, name="filename")
        self.directory = soft_signal_rw(str, name="directory")
        self.last_saved_path = soft_signal_rw(str, name="last_saved_path")

        self.add_readables(
            [self.last_saved_path], format=StandardReadableFormat.HINTED_SIGNAL
        )
        super().__init__(name=name)

    async def _write_image(self, file_path: str, image: ByteString):
        async with aiofiles.open(file_path, "wb") as file:
            await file.write(image)

    async def _get_and_write_image(self, file_path: str):
        async with ClientSession() as session:
            async with session.get(self.url) as response:
                if not response.ok:
                    LOGGER.warning(
                        f"Webcam responded with {response.status}: {response.reason}. Attempting to read anyway."
                    )
                try:
                    data = await response.read()
                    LOGGER.info(f"Saving webcam image from {self.url} to {file_path}")
                except Exception as e:
                    LOGGER.warning(
                        f"Failed to read data from {self.url} ({e}). Using placeholder image."
                    )
                    data = create_placeholder_image()

                await self._write_image(file_path, data)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        filename = await self.filename.get_value()
        directory = await self.directory.get_value()

        file_path = Path(f"{directory}/{filename}.{IMAGE_FORMAT}").as_posix()
        await self._get_and_write_image(file_path)
        await self.last_saved_path.set(file_path)
