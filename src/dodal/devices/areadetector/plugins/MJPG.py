import os
import threading
from abc import ABC, abstractmethod
from pathlib import Path

import requests
from ophyd import Component, Device, DeviceStatus, EpicsSignal, EpicsSignalRO, Signal
from PIL import Image, ImageDraw

from dodal.devices.oav.oav_parameters import OAVConfigParams
from dodal.log import LOGGER


class MJPG(Device, ABC):
    """The MJPG areadetector plugin creates an MJPG video stream of the camera's output.

    This devices uses that stream to grab images. When it is triggered it will send the
    latest image from the stream to the `post_processing` method for child classes to handle.
    """

    filename = Component(Signal)
    directory = Component(Signal)
    last_saved_path = Component(Signal)
    url = Component(EpicsSignal, "JPG_URL_RBV", string=True)
    x_size = Component(EpicsSignalRO, "ArraySize1_RBV")
    y_size = Component(EpicsSignalRO, "ArraySize2_RBV")
    input_rbpv = Component(EpicsSignalRO, "NDArrayPort_RBV")
    input_plugin = Component(EpicsSignal, "NDArrayPort")

    # scaling factors for the snapshot at the time it was triggered
    microns_per_pixel_x = Component(Signal)
    microns_per_pixel_y = Component(Signal)

    oav_params: OAVConfigParams | None = None

    KICKOFF_TIMEOUT: float = 30.0

    def _save_image(self, image: Image.Image):
        """A helper function to save a given image to the path supplied by the directory
        and filename signals. The full resultant path is put on the last_saved_path signal
        """
        filename_str = self.filename.get()
        directory_str: str = self.directory.get()  # type: ignore

        path = Path(f"{directory_str}/{filename_str}.png").as_posix()
        if not os.path.isdir(Path(directory_str)):
            LOGGER.info(f"Snapshot folder {directory_str} does not exist, creating...")
            os.mkdir(directory_str)

        LOGGER.info(f"Saving image to {path}")
        image.save(path)
        self.last_saved_path.put(path)

    def trigger(self):
        """This takes a snapshot image from the MJPG stream and send it to the
        post_processing method, expected to be implemented by a child of this class.

        It is the responsibility of the child class to save any resulting images.
        """
        st = DeviceStatus(device=self, timeout=self.KICKOFF_TIMEOUT)
        url_str = self.url.get()

        assert isinstance(
            self.oav_params, OAVConfigParams
        ), "MJPG does not have valid OAV parameters"
        self.microns_per_pixel_x.set(self.oav_params.micronsPerXPixel)
        self.microns_per_pixel_y.set(self.oav_params.micronsPerYPixel)

        def get_snapshot():
            try:
                response = requests.get(url_str, stream=True)
                response.raise_for_status()
                with Image.open(response.raw) as image:
                    self.post_processing(image)
                    st.set_finished()
            except requests.HTTPError as e:
                st.set_exception(e)

        threading.Thread(target=get_snapshot, daemon=True).start()

        return st

    @abstractmethod
    def post_processing(self, image: Image.Image):
        pass


class SnapshotWithBeamCentre(MJPG):
    """A child of MJPG which, when triggered, draws a crosshair at the beam centre in the
    image and saves the image to disk."""

    CROSSHAIR_LENGTH_PX = 20
    CROSSHAIR_COLOUR = "Blue"

    def post_processing(self, image: Image.Image):
        assert (
            self.oav_params is not None
        ), "Snapshot device does not have valid OAV parameters"
        beam_x = self.oav_params.beam_centre_i
        beam_y = self.oav_params.beam_centre_j

        draw = ImageDraw.Draw(image)
        HALF_LEN = self.CROSSHAIR_LENGTH_PX / 2
        draw.line(
            ((beam_x, beam_y - HALF_LEN), (beam_x, beam_y + HALF_LEN)),
            fill=self.CROSSHAIR_COLOUR,
        )
        draw.line(
            ((beam_x - HALF_LEN, beam_y), (beam_x + HALF_LEN, beam_y)),
            fill=self.CROSSHAIR_COLOUR,
        )

        self._save_image(image)
