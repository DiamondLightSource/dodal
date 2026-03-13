from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    DetectorArmLogic,
)
from ophyd_async.epics.adcore import (
    # DEFAULT_GOOD_STATES,
    ADBaseIO,
    # ADImageMode,
    # ADState,
    prepare_exposures,
)
from ophyd_async.epics.core import stop_busy_record

from dodal.devices.controllers import ConstantDeadTimeTriggerLogic


class MerlinTriggerLogic(ConstantDeadTimeTriggerLogic):
    def __init__(
        self,
        driver: ADBaseIO,
        # good_states: frozenset[ADState] = DEFAULT_GOOD_STATES,
    ) -> None:
        self.driver = driver
        # self.good_states = good_states

    #     self.frame_timeout: float = 0
    #     self._arm_status: AsyncStatus | None = None
    #     for drv_child in self.driver.children():
    #         logging.debug(drv_child)

    #     super().__init__(driver, 0.002)

    # async def prepare(self, trigger_info: TriggerInfo):
    #     self.frame_timeout = (
    #         DEFAULT_TIMEOUT + await self.driver.acquire_time.get_value()
    #     )
    #     await asyncio.gather(
    #         self.driver.num_images.set(trigger_info.number_of_exposures),
    #         self.driver.image_mode.set(ADImageMode.MULTIPLE),
    #     )

    # async def wait_for_idle(self):
    #     if self._arm_status:
    #         await self._arm_status

    # async def disarm(self):
    #     # We can't use caput callback as we already used it in arm() and we can't have
    #     # 2 or they will deadlock
    #     await stop_busy_record(self.driver.acquire, timeout=1)

    def get_deadtime(self, config_values) -> float:
        return 0.002

    async def prepare_internal(self, num: int, livetime: float, deadtime: float):
        await prepare_exposures(self.driver, num, livetime, deadtime)


class MerlinArmLogic(DetectorArmLogic):
    def __init__(self, driver: ADBaseIO) -> None:
        self.driver = driver
        self._arm_status: AsyncStatus | None = None

    async def arm(self):
        self._arm_status = await self.driver.acquire.set(True, timeout=DEFAULT_TIMEOUT)

    async def wait_for_idle(self):
        if self._arm_status:
            await self._arm_status

    async def disarm(self):
        await stop_busy_record(self.driver.acquire, timeout=1)
