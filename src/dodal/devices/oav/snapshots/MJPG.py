import threading
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path

import requests
from bluesky.protocols import Triggerable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    completed_status,
    soft_signal_rw,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw
from PIL import Image  # , ImageDraw

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

        # scaling factors for the snapshot at the time it was triggered
        self.microns_per_pixel_x = soft_signal_rw(float)
        self.microns_per_pixel_y = soft_signal_rw(float)

        # May not need this one
        # self.oav_params = None  (OAVConfig)

        self.KICKOFF_TIMEOUT = 30.0

        super().__init__(name)

    async def _save_image(self, image: Image.Image):
        """A helper function to save a given image to the path supplied by the \
            directory and filename signals. The full resultant path is put on the \
            last_saved_path signal
        """
        filename_str = await self.filename.get_value()
        directory_str = await self.directory.get_value()

        path = Path(f"{directory_str}/{filename_str}.png").as_posix()
        if not Path(directory_str).is_dir():
            LOGGER.info(f"Snapshot folder {directory_str} does not exist, creating...")
            Path(directory_str).mkdir(parents=True)

        LOGGER.info(f"Saving image to {path}")
        image.save(path)
        await self.last_saved_path.set(path, wait=True)

    @AsyncStatus.wrap
    async def trigger(self):
        """This takes a snapshot image from the MJPG stream and send it to the
        post_processing method, expected to be implemented by a child of this class.

        It is the responsibility of the child class to save any resulting images.
        """
        # TODO Figure out status!!!
        # status = AsyncStatus(self)
        url_str = await self.url.get_value()

        # For now, let's assume I set microns_per_pixels in the oav from those values
        def get_snapshot():
            try:
                response = requests.get(url_str, stream=True)
                response.raise_for_status()
                with Image.open(BytesIO(response.content)) as image:
                    self.post_processing(image)
                    completed_status()
                    # st.set_finished()
            except requests.HTTPError as e:
                completed_status(exception=e)
                # st.set_exception(e)

        threading.Thread(target=get_snapshot, daemon=True).start()

        # return st

    @abstractmethod
    def post_processing(self, image: Image.Image):
        pass
