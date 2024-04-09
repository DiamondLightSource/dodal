import asyncio
from typing import Optional, Set  # , Set

from ophyd_async.core import AsyncStatus, DetectorControl, DetectorTrigger
from ophyd_async.epics.areadetector.drivers.ad_base import (
    DEFAULT_GOOD_STATES,
    DetectorState,
    start_acquiring_driver_and_ensure_status,
)
from ophyd_async.epics.areadetector.utils import ImageMode, stop_busy_record

from drivers.pimte1_driver import Pimte1Driver

TRIGGER_MODE = {
    DetectorTrigger.internal: Pimte1Driver.TriggerMode.internal,
    DetectorTrigger.constant_gate: Pimte1Driver.TriggerMode.ext_trigger,
    DetectorTrigger.variable_gate: Pimte1Driver.TriggerMode.ext_trigger,
}


class PimteController(DetectorControl):
    def __init__(
        self,
        driver: Pimte1Driver,
        good_states: Set[DetectorState] = set(DEFAULT_GOOD_STATES),
    ) -> None:
        self.driver = driver
        self.good_states = good_states

    def get_deadtime(self, exposure: float) -> float:
        return exposure + 0.1

    async def _process_setting(self) -> None:
        await self.driver.initialize.set(1)

    async def set_temperature(self, temperature: float) -> None:
        await self.driver.set_temperture.set(temperature)
        await self._process_setting()

    async def set_speed(self, speed: Pimte1Driver.SpeedMode) -> None:
        await self.driver.speed.set(speed)
        await self._process_setting()

    async def arm(
        self,
        num: int = 1,
        trigger: DetectorTrigger = DetectorTrigger.internal,
        exposure: Optional[float] = None,
    ) -> AsyncStatus:

        funcs = [
            self.driver.num_images.set(999_999 if num == 0 else num),
            self.driver.image_mode.set(ImageMode.multiple),
            self.driver.trigger_mode.set(TRIGGER_MODE[trigger]),
        ]
        if exposure is not None:
            funcs.append(self.driver.acquire_time.set(exposure))

        await asyncio.gather(*funcs)
        await self._process_setting()
        return await start_acquiring_driver_and_ensure_status(
            self.driver, good_states=self.good_states
        )

    async def disarm(self):
        await stop_busy_record(self.driver.acquire, False, timeout=1)
