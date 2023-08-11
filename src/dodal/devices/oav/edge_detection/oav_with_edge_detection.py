import asyncio
import time
from typing import Callable, Final, Optional, Tuple, TypeVar

import numpy as np
from numpy.typing import NDArray
from ophyd.v2.core import AsyncStatus, StandardReadable
from ophyd.v2.epics import SignalR, SignalRW, epics_signal_r

from dodal.devices.oav.edge_detection.edge_detect_utils import (
    NONE_VALUE as INVALID_POSITION_VALUE,
)
from dodal.devices.oav.edge_detection.edge_detect_utils import (
    ArrayProcessingFunctions,
    MxSampleDetect,
)
from dodal.log import LOGGER

T = TypeVar("T")


class EdgeDetection(StandardReadable):
    INVALID_POSITION: Final[Tuple[int, int]] = (
        INVALID_POSITION_VALUE,
        INVALID_POSITION_VALUE,
    )

    def __init__(self, prefix, name: str = ""):
        self.array_data: SignalR[NDArray[np.uint8]] = epics_signal_r(
            NDArray[np.uint8], "pva://{}PVA:ARRAY".format(prefix)
        )

        self.oav_width: SignalR[int] = epics_signal_r(
            int, "{}PVA:ArraySize1_RBV".format(prefix)
        )
        self.oav_height: SignalR[int] = epics_signal_r(
            int, "{}PVA:ArraySize2_RBV".format(prefix)
        )

        self.timeout: float = 10.0

        self.preprocess: Callable[
            [np.ndarray], np.ndarray
        ] = ArrayProcessingFunctions.identity()
        self.canny_upper: int = 100
        self.canny_lower: int = 50
        self.close_ksize: int = 5
        self.close_iterations: int = 5
        self.scan_direction: int = 1
        self.min_tip_height: int = 5

        self.set_readable_signals(
            read=[
                self.array_data,
                self.oav_width,
                self.oav_height,
            ],
            config=[],
        )

        super().__init__(name=name)

    async def _get_tip_position(self) -> Tuple[Optional[int], Optional[int]]:
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
            array_data: NDArray[np.uint8] = await self.array_data.get_value()
            height: int = await self.oav_height.get_value()
            width: int = await self.oav_width.get_value()

            num_pixels: int = height * width  # type: ignore
            value_len = array_data.shape[0]
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
            LOGGER.warning(
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

        return (tip_x, tip_y)

    async def read(self) -> Tuple[int | None, int | None]:
        return await asyncio.wait_for(self._get_tip_position(), timeout=self.timeout)


if __name__ == "__main__":
    # with DeviceCollector():
    x = EdgeDetection(prefix="BL02J-DI-OAV-01:")

    async def acquire():
        await x.connect()
        img = await x.array_data.read()
        tip = await x.read()
        return img, tip

    img, tip = asyncio.get_event_loop().run_until_complete(
        asyncio.wait_for(acquire(), timeout=10)
    )
    print("Tip: {}".format(tip))
    import matplotlib.pyplot as plt

    plt.imshow(img[""]["value"].reshape(2176, 2112, 3))
    plt.show()
