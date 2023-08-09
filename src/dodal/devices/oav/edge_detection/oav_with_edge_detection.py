from dodal.devices.oav.oav_detector import OAV
from dodal.devices.oav.edge_detection.edge_detect_utils import MxSampleDetect, ArrayProcessingFunctions, NONE_VALUE as INVALID_POSITION_VALUE, SampleLocation
from dodal.log import LOGGER
from typing import TYPE_CHECKING, Callable, Final, Tuple, TypeVar, Optional, Type, Dict, Any

from ophyd.v2.core import AsyncStatus, StandardReadable, DeviceCollector
from ophyd.v2.epics import epics_signal_r, SignalR, SignalRW

import numpy as np
from numpy.typing import NDArray

import asyncio

from ophyd.v2 import _p4p
from ophyd.v2._p4p import make_converter as default_make_converter, get_unique, PvaConverter, PvaArrayConverter, get_dtype


class PvaNDArrayConverter(PvaConverter):
    def write_value(self, value):
        return value

    def value(self, value):
        return value["value"]

    def reading(self, value):
        return dict(
            value=self.value(value),
            timestamp=0,
            alarm_severity=0,
        )

# TODO: HACK!
def make_converter(datatype: Optional[Type], values: Dict[str, Any]) -> PvaConverter:
    pv = list(values)[0]
    typeid = get_unique({k: v.getID() for k, v in values.items()}, "typeids")
    typ = get_unique({k: type(v["value"]) for k, v in values.items()}, "value types")

    if "NTNDArray" in typeid:
        pv_dtype = get_unique(
            {k: v["value"].dtype for k, v in values.items()}, "dtypes"
        )
        # This is an array
        if datatype:
            # Check we wanted an array of this type
            dtype = get_dtype(datatype)
            if not dtype:
                raise TypeError(f"{pv} has type [{pv_dtype}] not {datatype.__name__}")
            if dtype != pv_dtype:
                raise TypeError(f"{pv} has type [{pv_dtype}] not [{dtype}]")
        return PvaNDArrayConverter()

    return default_make_converter(datatype, values)

_p4p.make_converter = make_converter


T = TypeVar('T')

class _SoftSignal(SignalRW[T]):
    def __init__(self, initial_value: T):
        self.value: T = initial_value

    async def _set(self, value: T):
        self.value = value

    def set(self, value: T, wait=True, timeout=None) -> AsyncStatus:
        coro = self._set(value)
        return AsyncStatus(coro)
    
    def read(self) -> T:
        if self.value is None:
            raise ValueError("Soft signal read before being set")
        return self.value


class EdgeDetection(StandardReadable):

    INVALID_POSITION: Final[Tuple[int, int]] = (INVALID_POSITION_VALUE, INVALID_POSITION_VALUE)

    def __init__(self, prefix, name: str = ""):
        self.array_data: SignalR[NDArray] = epics_signal_r(NDArray[np.uint8], "pva://{}PVA:ARRAY".format(prefix))

        # self.triggered_tip: SignalRW[Tuple[int | None, int | None]] = _SoftSignal(initial_value=EdgeDetection.INVALID_POSITION)

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

        self.set_readable_signals(
            read=[
                self.array_data
            ],
            config=[
                # self.triggered_tip
            ],
        )

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
            tip_x = None
            tip_y = None

        self.triggered_tip.set((tip_x, tip_y))

    async def read(self) -> Tuple[int | None, int | None]:
        # Clear last value
        self.triggered_tip.set(EdgeDetection.INVALID_POSITION)

        self.update_tip_position(value=self.array_data.get_value())
        return await self.triggered_tip.get_value()

    
if __name__ == "__main__":
    # with DeviceCollector():
    x = EdgeDetection(prefix="BL03I-DI-OAV-01:")

    async def doit():
        await x.connect()
        data = await x.array_data.read()
        print(data)
        return data

    img = asyncio.get_event_loop().run_until_complete(doit())

    print(img)
