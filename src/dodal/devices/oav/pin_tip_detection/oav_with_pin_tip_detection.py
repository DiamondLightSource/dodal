import asyncio
import time
from collections import OrderedDict
from typing import Callable, Optional, Tuple, Type, TypeVar

import numpy as np
from bluesky.protocols import Descriptor
from numpy.typing import NDArray
from ophyd.v2.core import Device, Readable, Reading, SimConverter, SimSignalBackend
from ophyd.v2.epics import SignalR, SignalRW, epics_signal_r

from dodal.devices.oav.pin_tip_detection.pin_tip_detect_utils import (
    ArrayProcessingFunctions,
    MxSampleDetect,
)
from dodal.log import LOGGER

T = TypeVar("T")


def _create_soft_signal(
    name: str, datatype: T | Type[T], initial_value: T
) -> SignalRW[T]:
    class _Converter(SimConverter):
        def make_initial_value(self, *args, **kwargs) -> T:
            return initial_value

    class _SimSignalBackend(SimSignalBackend):
        async def connect(self) -> None:
            self.converter = _Converter()
            self._initial_value = self.converter.make_initial_value()
            self._severity = 0

            await self.put(None)

    backend = _SimSignalBackend(
        datatype, f"sim://oav_with_pin_tip_detection_soft_params:{name}"
    )
    signal: SignalRW[T] = SignalRW(backend)
    return signal


class PinTipDetection(Readable, Device):
    def __init__(self, prefix: str, name: str = ""):
        self._prefix: str = prefix
        self._name = name

        self.array_data: SignalR[NDArray[np.uint8]] = epics_signal_r(
            NDArray[np.uint8], f"pva://{prefix}PVA:ARRAY"
        )

        self.oav_width: SignalR[int] = epics_signal_r(
            int, f"{prefix}PVA:ArraySize1_RBV"
        )
        self.oav_height: SignalR[int] = epics_signal_r(
            int, f"{prefix}PVA:ArraySize2_RBV"
        )

        # Soft parameters for pin-tip detection.
        self.timeout: SignalRW[float] = _create_soft_signal("timeout", float, 10.0)
        self.preprocess: SignalRW[
            Callable[[np.ndarray], np.ndarray]
        ] = _create_soft_signal(
            "preprocess",
            Callable[[np.ndarray], np.ndarray],
            ArrayProcessingFunctions.identity(),
        )
        self.canny_upper: SignalRW[int] = _create_soft_signal("canny_upper", int, 100)
        self.canny_lower: SignalRW[int] = _create_soft_signal("canny_lower", int, 50)
        self.close_ksize: SignalRW[int] = _create_soft_signal("close_ksize", int, 5)
        self.close_iterations: SignalRW[int] = _create_soft_signal(
            "close_iterations", int, 5
        )
        self.scan_direction: SignalRW[int] = _create_soft_signal(
            "scan_direction", int, 1
        )
        self.min_tip_height: SignalRW[int] = _create_soft_signal(
            "min_tip_height", int, 5
        )

        super().__init__(name=name)

    async def _get_tip_position(
        self,
    ) -> Tuple[Tuple[Optional[int], Optional[int]], float]:
        """
        Gets the location of the pin tip.

        Returns tuple of:
            ((tip_x, tip_y), timestamp)
        """
        sample_detection = MxSampleDetect(
            preprocess=await self.preprocess.get_value(),
            canny_lower=await self.canny_lower.get_value(),
            canny_upper=await self.canny_upper.get_value(),
            close_ksize=await self.close_ksize.get_value(),
            close_iterations=await self.close_iterations.get_value(),
            scan_direction=await self.scan_direction.get_value(),
            min_tip_height=await self.min_tip_height.get_value(),
        )

        array_reading: dict[str, Reading] = await self.array_data.read()
        array_data: NDArray[np.uint8] = array_reading[""]["value"]
        timestamp: float = array_reading[""]["timestamp"]

        height: int = await self.oav_height.get_value()
        width: int = await self.oav_width.get_value()

        num_pixels: int = height * width  # type: ignore
        value_len = array_data.shape[0]

        try:
            if value_len == num_pixels * 3:
                # RGB data
                value = array_data.reshape(height, width, 3)
            elif value_len == num_pixels:
                # Grayscale data
                value = array_data.reshape(height, width)
            else:
                # Something else?
                raise ValueError(
                    "Unexpected data array size: expected {} (grayscale data) or {} (rgb data), got {}",
                    num_pixels,
                    num_pixels * 3,
                    value_len,
                )

            start_time = time.time()
            location = sample_detection.processArray(value)
            end_time = time.time()
            LOGGER.debug(
                "Sample location detection took {}ms".format(
                    (end_time - start_time) * 1000.0
                )
            )
            tip_x = location.tip_x
            tip_y = location.tip_y
        except Exception as e:
            LOGGER.error("Failed to detect pin-tip location due to exception: ", e)
            tip_x = None
            tip_y = None

        return (tip_x, tip_y), timestamp

    async def read(self) -> dict[str, Reading]:
        tip_pos, timestamp = await asyncio.wait_for(
            self._get_tip_position(), timeout=await self.timeout.get_value()
        )

        return OrderedDict(
            [
                (self._name, {"value": tip_pos, "timestamp": timestamp}),
            ]
        )

    async def describe(self) -> dict[str, Descriptor]:
        return OrderedDict(
            [
                (
                    self._name,
                    {
                        "source": "pva://{}PVA:ARRAY".format(self._prefix),
                        "dtype": "number",
                        "shape": [2],  # Tuple of (x, y) tip position
                    },
                )
            ],
        )


if __name__ == "__main__":
    x = PinTipDetection(prefix="BL03I-DI-OAV-01:", name="edgeDetect")

    async def acquire():
        await x.connect()
        img = await x.array_data.read()
        tip = await x.read()
        return img, tip

    img, tip = asyncio.get_event_loop().run_until_complete(
        asyncio.wait_for(acquire(), timeout=10)
    )
    print(tip)
    print("Tip: {}".format(tip["edgeDetect"]["value"]))

    try:
        import matplotlib.pyplot as plt

        plt.imshow(img[""]["value"].reshape(768, 1024, 3))
        plt.show()
    except ImportError:
        print("matplotlib not available; cannot show acquired image")
