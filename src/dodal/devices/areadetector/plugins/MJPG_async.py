from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path

import aiofiles
from aiohttp import ClientSession
from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_rw
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw
from PIL import Image

from dodal.log import LOGGER


class MJPG(StandardReadable, Triggerable, ABC):
    """The MJPG areadetector plugin creates an MJPG video stream of the camera's output.

    This devices uses that stream to grab images. When it is triggered it will send the
    latest image from the stream to the `post_processing` method for child classes to handle.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.filename = soft_signal_rw(str)
        self.directory = soft_signal_rw(str)
        self.last_saved_path = soft_signal_rw(str)

        self.url = epics_signal_rw(str, prefix + "JPG_URL_RBV")

        self.x_size = epics_signal_r(int, prefix + "ArraySize1_RBV")
        self.y_size = epics_signal_r(int, prefix + "ArraySize2_RBV")

        # TODO check type of these two
        self.input_rbpv = epics_signal_r(str, prefix + "NDArrayPort_RBV")
        self.input_plugin = epics_signal_rw(str, prefix + "NDArrayPort")

        self.KICKOFF_TIMEOUT = 30.0

        super().__init__(name)

    async def _save_image(self, image: Image.Image):
        """A helper function to save a given image to the path supplied by the \
            directory and filename signals. The full resultant path is put on the \
            last_saved_path signal
        """
        print("HERE 5.5")
        filename_str = await self.filename.get_value()
        directory_str = await self.directory.get_value()
        print("HERE 6")

        path = Path(f"{directory_str}/{filename_str}.png").as_posix()
        if not Path(directory_str).is_dir():
            LOGGER.info(f"Snapshot folder {directory_str} does not exist, creating...")
            Path(directory_str).mkdir(parents=True)

        LOGGER.info(f"Saving image to {path}")
        print("HERE 7")

        buffer = BytesIO()
        image.save(buffer, format="png")
        async with aiofiles.open(path, "wb") as fh:
            await fh.write(buffer.getbuffer())
        # image.save(path)
        await self.last_saved_path.set(path, wait=True)

    @AsyncStatus.wrap
    async def trigger(self):
        """This takes a snapshot image from the MJPG stream and send it to the
        post_processing method, expected to be implemented by a child of this class.

        It is the responsibility of the child class to save any resulting images.
        """
        url_str = await self.url.get_value()

        async with ClientSession() as session:
            async with session.get(url_str) as response:
                if not response.ok:
                    LOGGER.warning(
                        f"OAV responded with {response.status}: {response.reason}."
                    )
                try:
                    print("HERE 1")
                    data = await response.read()
                    print("HERE1.5")
                    with Image.open(BytesIO(data)) as image:
                       print("HERE 2")
                       await self.post_processing(image)
                except Exception as e:
                    LOGGER.warning(f"Failed to create snapshot. \n {e}")

    @abstractmethod
    async def post_processing(self, image: Image.Image):
        pass
