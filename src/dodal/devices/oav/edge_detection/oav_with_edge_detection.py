from dodal.devices.oav.oav_detector import OAV
from ophyd.signal import EpicsSignalRO, Signal, Kind
from ophyd.status import SubscriptionStatus
from ophyd import Component, Device
from dodal.devices.oav.edge_detection.edge_detect_utils import MxSampleDetect, ArrayProcessingFunctions, NONE_VALUE as INVALID_POSITION_VALUE, SampleLocation
from dodal.log import LOGGER
from typing import TYPE_CHECKING, Callable, Final, Tuple

from ophyd.v2.core import StandardReadable, DeviceCollector
from ophyd.v2.epics import epics_signal_r

import numpy as np
import numpy.typing


class AreaDetectorPvaPluginArray(StandardReadable):
    """
    An Ophyd v2 device wrapping the areadetector PVA plugin. Will fetch array data via PVA. 
    """
    
    def __init__(self, prefix: str, name: str = ""):

        self.array_data = epics_signal_r(numpy.typing.NDArray, "pva://{}ARR:ArrayData".format(prefix))

        self.set_readable_signals(
            read=[self.array_data],
            config=[],
        )
        super().__init__(name=name)


class EdgeDetection(StandardReadable):

    INVALID_POSITION: Final[Tuple[int, int]] = (INVALID_POSITION_VALUE, INVALID_POSITION_VALUE)

    def __init__(self, prefix, name: str = ""):
        
        self.array_data = epics_signal_r(numpy.typing.NDArray, "pva://{}ARR:ArrayData".format(prefix))

        with DeviceCollector():
            self.pva_array_data: StandardReadable = AreaDetectorPvaPluginArray(prefix=prefix)

        self.triggered_tip: Signal = Component(Signal, kind=Kind.hinted, value=INVALID_POSITION)  # type: ignore

        self.oav_width: int = 1024
        self.oav_height: int = 768

        self.timeout: float = 10.0

        self.preprocess: Callable[[np.ndarray], np.ndarray] = ArrayProcessingFunctions.identity()
        self.canny_upper: int = 100
        self.canny_lower: int = 50
        self.close_ksize: int = 5
        self.close_iterations: int = 5
        self.scan_direction: int = 1
        self.min_tip_height: int = 5

        super().__init__(name=name)

    def update_tip_position(self, *, value, **_):

        sample_detection = MxSampleDetect(
            preprocess=self.preprocess,
            canny_lower=self.canny_lower,
            canny_upper=self.canny_upper,
            close_ksize=self.close_ksize,
            close_iterations=self.close_iterations,
            scan_direction=self.scan_direction,
            min_tip_height=self.min_tip_height,
        )

        try:
            num_pixels = self.oav_height * self.oav_width
            value_len = value.shape[0]
            if value_len == num_pixels * 3:
                # RGB data
                value = value.reshape(self.oav_height, self.oav_width, 3)
            elif value_len == num_pixels:
                # Grayscale data
                value = value.reshape(self.oav_height, self.oav_width)
            else:
                # Something else?
                raise ValueError("Unexpected data array size: expected {} (grayscale data) or {} (rgb data), got {}", num_pixels, num_pixels * 3, value_len)
            
            location = sample_detection.processArray(value)
            tip_x = location.tip_x
            tip_y = location.tip_y
        except Exception as e:
            LOGGER.error("Failed to detect sample position: ", e)
            tip_x = INVALID_POSITION_VALUE
            tip_y = INVALID_POSITION_VALUE

        self.triggered_tip.put((tip_x, tip_y))

    def trigger(self) -> SubscriptionStatus:
        # Clear last value
        self.triggered_tip.put(INVALID_POSITION_VALUE)

        subscription_status = SubscriptionStatus(
            self.pva_array_data, self.update_tip_position, run=True, timeout=self.timeout
        )
        return subscription_status


class OAVWithEdgeDetection(OAV):
    edge_detect: Component[EdgeDetection] = Component(EdgeDetection, "-DI-OAV-01:")

    
if __name__ == "__main__":
    x = OAVWithEdgeDetection(name="oav", prefix="BL03I")
    x.wait_for_connection()
    img = x.edge_detect.array_data.get()
    with open("/scratch/beamline_i03_oav_image_temp", "wb") as f:
        np.save(f, img)

    import matplotlib.pyplot as plt
    plt.imshow(np.transpose(img.reshape(80, 80, 3), axes=[0, 1, 2]))
    plt.show()
