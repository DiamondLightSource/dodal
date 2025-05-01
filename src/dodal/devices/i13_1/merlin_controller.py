import asyncio
import logging

from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    TriggerInfo,
)
from ophyd_async.epics.adcore import (
    DEFAULT_GOOD_STATES,
    ADBaseController,
    ADBaseIO,
    ADImageMode,
    ADState,
    stop_busy_record,
)


class MerlinController(ADBaseController):
    def __init__(
        self,
        driver: ADBaseIO,
        good_states: frozenset[ADState] = DEFAULT_GOOD_STATES,
    ) -> None:
        self.driver = driver
        self.good_states = good_states
        self.frame_timeout: float = 0
        self._arm_status: AsyncStatus | None = None
        for drv_child in self.driver.children():
            logging.debug(drv_child)

    def get_deadtime(self, exposure: float | None) -> float:
        return 0.002

    async def prepare(self, trigger_info: TriggerInfo):
        self.frame_timeout = (
            DEFAULT_TIMEOUT + await self.driver.acquire_time.get_value()
        )
        await asyncio.gather(
            self.driver.num_images.set(trigger_info.total_number_of_exposures),
            self.driver.image_mode.set(ADImageMode.MULTIPLE),
        )

    async def wait_for_idle(self):
        if self._arm_status:
            await self._arm_status

    async def disarm(self):
        # We can't use caput callback as we already used it in arm() and we can't have
        # 2 or they will deadlock
        await stop_busy_record(self.driver.acquire, False, timeout=1)
