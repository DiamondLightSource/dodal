import asyncio
import time
from collections import OrderedDict
from typing import Callable, Optional, Tuple, TypeVar, Type

import numpy as np
from bluesky.protocols import Descriptor
from numpy.typing import NDArray
from ophyd.v2.core import Readable, Reading, Device
from ophyd.v2.epics import SignalR, epics_signal_r

from dodal.devices.oav.edge_detection.edge_detect_utils import (
    ArrayProcessingFunctions,
    MxSampleDetect,
)
from dodal.log import LOGGER

T = TypeVar("T")


class EdgeDetection(Readable, Device):
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
            preprocess=self.preprocess,
            canny_lower=self.canny_lower,
            canny_upper=self.canny_upper,
            close_ksize=self.close_ksize,
            close_iterations=self.close_iterations,
            scan_direction=self.scan_direction,
            min_tip_height=self.min_tip_height,
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
            self._get_tip_position(), timeout=self.timeout
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
    x = EdgeDetection(prefix="BL03I-DI-OAV-01:", name="edgeDetect")

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
