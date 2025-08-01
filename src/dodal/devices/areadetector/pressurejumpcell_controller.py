import asyncio

from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    DetectorTrigger,
    observe_value,
    set_and_wait_for_value,
    set_and_wait_for_other_value,
    TriggerInfo,
    wait_for_value,
)
from ophyd_async.epics import adcore

from .pressurejumpcell_io import (
    PressureJumpCellAdcTriggerIO,
    PressureJumpCellDriverIO,
    PressureJumpCellTriggerMode,
    AdcTriggerState,
)

# TODO Find out what the readout time is and if it can be retrieved from the device
PRESSURE_CELL_READAOUT_TIME = 1e-3
TRIG_GOOD_STATES: frozenset[AdcTriggerState] = frozenset([AdcTriggerState.IDLE])


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
        trig: PressureJumpCellAdcTriggerIO,
        good_states: frozenset[adcore.ADState] = adcore.DEFAULT_GOOD_STATES,
        readout_time: float = PRESSURE_CELL_READAOUT_TIME,
    ) -> None:
        super().__init__(driver, good_states=good_states)
        self._readout_time = readout_time
        self.trig: PressureJumpCellAdcTriggerIO = trig

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
            self.driver.image_mode.set(adcore.ADImageMode.CONTINUOUS),
        )

    async def arm(self):
        # Standard arm the detector and wait for the acquire PV to be True
        self._arm_status = await self.start_acquiring_driver_and_ensure_status()

    async def start_acquiring_driver_and_ensure_status(
        self,
        start_timeout: float = DEFAULT_TIMEOUT,
        state_timeout: float = DEFAULT_TIMEOUT,
    ) -> AsyncStatus:
        # Set Main ADC to acquire
        await set_and_wait_for_value(
            self.driver.acquire,
            True,
            timeout=start_timeout,
            wait_for_set_completion=False,
        )

        # Set trigger to capture
        status = await set_and_wait_for_other_value(
            self.trig.capture,
            True,
            self.trig.state,
            AdcTriggerState.ARMED,
            timeout=start_timeout,
            wait_for_set_completion=False,
        )

        async def complete_acquisition() -> None:
            await status
            state = None
            try:
                async for state in observe_value(
                    self.trig.state, done_timeout=state_timeout
                ):
                    if state in TRIG_GOOD_STATES:
                        return
            except asyncio.TimeoutError as exc:
                if state is not None:
                    raise ValueError(
                        f"Final detector state {state.value} not in valid end "
                        f"states: {self.good_states}"
                    ) from exc
                else:
                    # No updates from the detector, something else is wrong
                    raise asyncio.TimeoutError(
                        "Could not monitor detector state: "
                        + self.driver.detector_state.source
                    ) from exc

        return AsyncStatus(complete_acquisition())
