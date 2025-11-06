from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path

import aiofiles
from aiohttp import ClientSession
from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_rw
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw
from PIL import Image

from dodal.log import LOGGER

IMG_FORMAT = "png"


async def asyncio_save_image(image: Image.Image, path: str):
    buffer = BytesIO()
    image.save(buffer, format=IMG_FORMAT)
    async with aiofiles.open(path, "wb") as fh:
        await fh.write(buffer.getbuffer())


class MJPG(StandardReadable, Triggerable, ABC):
    """The MJPG areadetector plugin creates an MJPG video stream of the camera's output.

    This devices uses that stream to grab images. When it is triggered it will send the
    latest image from the stream to the `post_processing` method for child classes to handle.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.url = epics_signal_rw(str, prefix + "JPG_URL_RBV")

        self.x_size = epics_signal_r(int, prefix + "ArraySize1_RBV")
        self.y_size = epics_signal_r(int, prefix + "ArraySize2_RBV")

        with self.add_children_as_readables():
            self.filename = soft_signal_rw(str)
            self.directory = soft_signal_rw(str)
            self.last_saved_path = soft_signal_rw(str)

        self.KICKOFF_TIMEOUT = 30.0

        super().__init__(name)

    async def _save_image(self, image: Image.Image):
        """A helper function to save a given image to the path supplied by the \
            directory and filename signals. The full resultant path is put on the \
            last_saved_path signal
        """
        filename_str = await self.filename.get_value()
        directory_str = await self.directory.get_value()

        path = Path(f"{directory_str}/{filename_str}.{IMG_FORMAT}").as_posix()
        if not Path(directory_str).is_dir():
            LOGGER.info(f"Snapshot folder {directory_str} does not exist, creating...")
            Path(directory_str).mkdir(parents=True)

        LOGGER.info(f"Saving image to {path}")

        await asyncio_save_image(image, path)

        await self.last_saved_path.set(path, wait=True)

    @AsyncStatus.wrap
    async def trigger(self):
        """This takes a snapshot image from the MJPG stream and send it to the
        post_processing method, expected to be implemented by a child of this class.

        It is the responsibility of the child class to save any resulting images by \
        calling _save_image.
        """
        url_str = await self.url.get_value()

        async with ClientSession(raise_for_status=True) as session:
            async with session.get(url_str) as response:
                data = await response.read()
                with Image.open(BytesIO(data)) as image:
                    await self.post_processing(image)

    @abstractmethod
    async def post_processing(self, image: Image.Image):
        pass
