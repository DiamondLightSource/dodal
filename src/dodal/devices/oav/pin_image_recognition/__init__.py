import asyncio
import time

import numpy as np
from numpy.typing import NDArray
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    StandardReadable,
    observe_value,
)
from ophyd_async.epics.signal import epics_signal_r

from dodal.devices.oav.pin_image_recognition.utils import (
    ARRAY_PROCESSING_FUNCTIONS_MAP,
    MxSampleDetect,
    SampleLocation,
    ScanDirections,
    identity,
)
from dodal.devices.ophyd_async_utils import create_soft_signal_r, create_soft_signal_rw
from dodal.log import LOGGER

Tip = tuple[int | None, int | None]


class InvalidPinException(Exception):
    pass


class PinTipDetection(StandardReadable):
    """
    A device which will read from an on-axis view and calculate the location of the
    pin-tip (in pixels) of that frame.

    Used for pin tip centring workflow.

    Note that if the tip of the sample is off-screen, this class will return the tip as
    the "edge" of the image.

    If no tip is found it will return {INVALID_POSITION}. However, it will also
    occasionally give incorrect data. Therefore, it is recommended that you trigger
    this device, which will attempt to find a pin within {validity_timeout} seconds if
    no tip is found after this time it will not error but instead return {INVALID_POSITION}.
    """

    INVALID_POSITION = (None, None)

    def __init__(self, prefix: str, name: str = ""):
        self._prefix: str = prefix
        self._name = name

        self.triggered_tip = create_soft_signal_r(Tip, "triggered_tip", self.name)
        self.triggered_top_edge = create_soft_signal_r(
            NDArray[np.uint32], "triggered_top_edge", self.name
        )
        self.triggered_bottom_edge = create_soft_signal_r(
            NDArray[np.uint32], "triggered_bottom_edge", self.name
        )
        self.array_data = epics_signal_r(NDArray[np.uint8], f"pva://{prefix}PVA:ARRAY")

        # Soft parameters for pin-tip detection.
        self.preprocess_operation = create_soft_signal_rw(int, "preprocess", self.name)
        self.preprocess_ksize = create_soft_signal_rw(
            int, "preprocess_ksize", self.name
        )
        self.preprocess_iterations = create_soft_signal_rw(
            int, "preprocess_iterations", self.name
        )
        self.canny_upper_threshold = create_soft_signal_rw(
            int, "canny_upper", self.name
        )
        self.canny_lower_threshold = create_soft_signal_rw(
            int, "canny_lower", self.name
        )
        self.close_ksize = create_soft_signal_rw(int, "close_ksize", self.name)
        self.close_iterations = create_soft_signal_rw(
            int, "close_iterations", self.name
        )
        self.scan_direction = create_soft_signal_rw(int, "scan_direction", self.name)
        self.min_tip_height = create_soft_signal_rw(int, "min_tip_height", self.name)
        self.validity_timeout = create_soft_signal_rw(
            float, "validity_timeout", self.name
        )

        self.set_readable_signals(
            read=[
                self.triggered_tip,
                self.triggered_top_edge,
                self.triggered_bottom_edge,
            ],
        )

        super().__init__(name=name)

    async def _set_triggered_values(self, results: SampleLocation):
        tip = (results.tip_x, results.tip_y)
        if tip == self.INVALID_POSITION:
            raise InvalidPinException
        else:
            await self.triggered_tip._backend.put(tip)
        await self.triggered_top_edge._backend.put(results.edge_top)
        await self.triggered_bottom_edge._backend.put(results.edge_bottom)

    async def _get_tip_and_edge_data(
        self, array_data: NDArray[np.uint8]
    ) -> SampleLocation:
        """
        Gets the location of the pin tip and the top and bottom edges.
        """
        preprocess_key = await self.preprocess_operation.get_value()
        preprocess_iter = await self.preprocess_iterations.get_value()
        preprocess_ksize = await self.preprocess_ksize.get_value()

        try:
            preprocess_func = ARRAY_PROCESSING_FUNCTIONS_MAP[preprocess_key](
                iter=preprocess_iter, ksize=preprocess_ksize
            )
        except KeyError:
            LOGGER.error("Invalid preprocessing function, using identity")
            preprocess_func = identity()

        direction = (
            ScanDirections.FORWARD
            if await self.scan_direction.get_value() == 0
            else ScanDirections.REVERSE
        )

        sample_detection = MxSampleDetect(
            preprocess=preprocess_func,
            canny_lower=await self.canny_lower_threshold.get_value(),
            canny_upper=await self.canny_upper_threshold.get_value(),
            close_ksize=await self.close_ksize.get_value(),
            close_iterations=await self.close_iterations.get_value(),
            scan_direction=direction,
            min_tip_height=await self.min_tip_height.get_value(),
        )

        start_time = time.time()
        location = sample_detection.processArray(array_data)
        end_time = time.time()
        LOGGER.debug(
            "Sample location detection took {}ms".format(
                (end_time - start_time) * 1000.0
            )
        )
        return location

    async def connect(self, sim: bool = False, timeout: float = DEFAULT_TIMEOUT):
        await super().connect(sim, timeout)

        # Set defaults for soft parameters
        await self.validity_timeout.set(5.0)
        await self.canny_upper_threshold.set(100)
        await self.canny_lower_threshold.set(50)
        await self.close_iterations.set(5)
        await self.close_ksize.set(5)
        await self.scan_direction.set(ScanDirections.FORWARD.value)
        await self.min_tip_height.set(5)
        await self.preprocess_operation.set(10)  # Identity function
        await self.preprocess_iterations.set(5)
        await self.preprocess_ksize.set(5)

    @AsyncStatus.wrap
    async def trigger(self):
        async def _set_triggered_tip():
            """Monitors the camera data and updates the triggered_tip signal.

            If a tip is found it will update the signal and stop monitoring
            If no tip is found it will retry with the next monitored value
            This loop will serve as a good example of using 'observe_value' in the ophyd_async documentation
            """
            async for value in observe_value(self.array_data):
                try:
                    location = await self._get_tip_and_edge_data(value)
                    await self._set_triggered_values(location)
                except Exception as e:
                    LOGGER.warn(
                        f"Failed to detect pin-tip location, will retry with next image: {e}"
                    )
                else:
                    return

        try:
            await asyncio.wait_for(
                _set_triggered_tip(), timeout=await self.validity_timeout.get_value()
            )
        except asyncio.exceptions.TimeoutError:
            LOGGER.error(
                f"No tip found in {await self.validity_timeout.get_value()} seconds."
            )
            await self.triggered_tip._backend.put(self.INVALID_POSITION)
            await self.triggered_bottom_edge._backend.put(np.array([]))
            await self.triggered_top_edge._backend.put(np.array([]))
