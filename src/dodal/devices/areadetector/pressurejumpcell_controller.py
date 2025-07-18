import asyncio

from ophyd_async.core import (
    DetectorTrigger,
    TriggerInfo,
)
from ophyd_async.epics import adcore

from .pressurejumpcell_io import (
    PressureJumpCellDriverIO,
    PressureJumpCellTriggerMode,
)

#TODO Find out what the readout time is and if it can be retrieved from the device
PRESSURE_CELL_READAOUT_TIME = 1e-3


class PressureJumpCellController(adcore.ADBaseController[PressureJumpCellDriverIO]):
    """`DetectorController` for a `PressureJumpCellDriverIO`."""

    _supported_trigger_types = {
        DetectorTrigger.INTERNAL: PressureJumpCellTriggerMode.INTERNAL,
        DetectorTrigger.CONSTANT_GATE: PressureJumpCellTriggerMode.EXTERNAL,
        DetectorTrigger.EDGE_TRIGGER: PressureJumpCellTriggerMode.EXTERNAL,
        DetectorTrigger.VARIABLE_GATE: PressureJumpCellTriggerMode.EXTERNAL,
    }

    def __init__(
        self,
        driver: PressureJumpCellDriverIO,
        good_states: frozenset[adcore.ADState] = adcore.DEFAULT_GOOD_STATES,
        readout_time: float = PRESSURE_CELL_READAOUT_TIME,
    ) -> None:
        super().__init__(driver, good_states=good_states)
        self._readout_time = readout_time

    def get_deadtime(self, exposure: float | None) -> float:
        return self._readout_time

    async def prepare(self, trigger_info: TriggerInfo):
        if trigger_info.livetime is not None:
            await self.set_exposure_time_and_acquire_period_if_supplied(
                trigger_info.livetime
            )
        await asyncio.gather(
            self.driver.trigger_mode.set(
                self._supported_trigger_types[trigger_info.trigger]
            ),
            self.driver.num_images.set(
                999_999
                if trigger_info.total_number_of_exposures == 0
                else trigger_info.total_number_of_exposures
            ),
            self.driver.image_mode.set(adcore.ADImageMode.MULTIPLE),
        )

    async def arm(self):
        # Standard arm the detector and wait for the acquire PV to be True
        self._arm_status = await self.start_acquiring_driver_and_ensure_status()
