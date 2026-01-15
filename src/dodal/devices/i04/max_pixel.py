import numpy as np
from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.core import (
    epics_signal_r,
)

from dodal.devices.oav.utils import convert_to_gray_and_blur


class MaxPixel(StandardReadable, Triggerable):
    """Gets the max pixel (brightest pixel) from the image after some image processing."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.array_data = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")
        self.max_pixel_val, self._max_val_setter = soft_signal_r_and_setter(float)
        super().__init__(name)

    @AsyncStatus.wrap
    async def trigger(self):
        img_data = await self.array_data.get_value()
        arr = convert_to_gray_and_blur(img_data)
        max_val = float(np.max(arr))
        assert isinstance(max_val, float)
        self._max_val_setter(max_val)
