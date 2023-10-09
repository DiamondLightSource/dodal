import threading
from pathlib import Path

import requests
from ophyd import Component, Device, DeviceStatus, EpicsSignal, EpicsSignalRO, Signal
from PIL import Image

from dodal.log import LOGGER


class MJPG(Device):
    filename: Signal = Component(Signal)
    directory: Signal = Component(Signal)
    last_saved_path: Signal = Component(Signal)
    url: EpicsSignal = Component(EpicsSignal, "JPG_URL_RBV", string=True)
    x_size: EpicsSignalRO = Component(EpicsSignalRO, "ArraySize1_RBV")
    y_size: EpicsSignalRO = Component(EpicsSignalRO, "ArraySize2_RBV")
    input_rbpv: EpicsSignalRO = Component(EpicsSignalRO, "NDArrayPort_RBV")
    input_plugin: EpicsSignal = Component(EpicsSignal, "NDArrayPort")
    KICKOFF_TIMEOUT: float = 30.0

    def trigger(self):
        st = DeviceStatus(device=self, timeout=self.KICKOFF_TIMEOUT)
        url_str = self.url.get()
        filename_str = self.filename.get()
        directory_str = self.directory.get()

        def get_snapshot():
            try:
                response = requests.get(url_str, stream=True)
                response.raise_for_status()
                image = Image.open(response.raw)
                path = Path(f"{directory_str}/{filename_str}.png").as_posix()
                self.last_saved_path.put(path)
                LOGGER.info(f"Saving {path}")
                image.save(path)
                self.post_processing(image)
                st.set_finished()
            except requests.HTTPError as e:
                st.set_exception(e)

        threading.Thread(target=get_snapshot, daemon=True).start()

        return st

    def post_processing(self, image: Image.Image):
        pass
