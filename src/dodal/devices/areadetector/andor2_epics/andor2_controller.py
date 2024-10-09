import asyncio

from ophyd_async.core import DetectorControl, DetectorTrigger
from ophyd_async.core._detector import TriggerInfo
from ophyd_async.epics import adcore
from ophyd_async.epics.adcore import (
    DEFAULT_GOOD_STATES,
    DetectorState,
    stop_busy_record,
)

from .andor2_io import (
    Andor2DriverIO,
    Andor2TriggerMode,
    ImageMode,
)

MIN_DEAD_TIME = 0.1
DEFAULT_MAX_NUM_IMAGE = 999_999


class Andor2Controller(DetectorControl):
    _supported_trigger_types = {
        DetectorTrigger.internal: Andor2TriggerMode.internal,
        DetectorTrigger.edge_trigger: Andor2TriggerMode.ext_trigger,
    }

    def __init__(
        self,
        driver: Andor2DriverIO,
        good_states: set[DetectorState] | None = None,
    ) -> None:
        if good_states is None:
            good_states = set(DEFAULT_GOOD_STATES)
        self._drv = driver
        self.good_states = good_states

    def get_deadtime(self, exposure: float | None) -> float:
        if exposure is None:
            return MIN_DEAD_TIME
        return exposure + MIN_DEAD_TIME

    async def prepare(self, trigger_info: TriggerInfo):
        if trigger_info.livetime is not None:
            await adcore.set_exposure_time_and_acquire_period_if_supplied(
                self, self._drv, trigger_info.livetime
            )
        await asyncio.gather(
            self._drv.trigger_mode.set(self._get_trigger_mode(trigger_info.trigger)),
            self._drv.num_images.set(
                DEFAULT_MAX_NUM_IMAGE
                if trigger_info.number == 0
                else trigger_info.number
            ),
            self._drv.image_mode.set(ImageMode.multiple),
        )

    async def arm(self) -> None:
        # Standard arm the detector and wait for the acquire PV to be True
        self._arm_status = await adcore.start_acquiring_driver_and_ensure_status(
            self._drv
        )

    async def wait_for_idle(self):
        if self._arm_status:
            await self._arm_status

    @classmethod
    def _get_trigger_mode(cls, trigger: DetectorTrigger) -> Andor2TriggerMode:
        if trigger not in cls._supported_trigger_types.keys():
            raise ValueError(
                f"{cls.__name__} only supports the following trigger "
                f"types: {cls._supported_trigger_types.keys()} but was asked to "
                f"use {trigger}"
            )
        return cls._supported_trigger_types[trigger]

    async def disarm(self):
        await stop_busy_record(self._drv.acquire, False, timeout=1)
