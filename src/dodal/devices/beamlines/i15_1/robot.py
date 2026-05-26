import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from functools import partial

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    DeviceMock,
    SignalX,
    StandardReadable,
    StrictEnum,
    callback_on_mock_put,
    default_mock_class,
    derived_signal_rw,
    set_and_wait_for_value,
    set_mock_value,
    wait_for_value,
)
from ophyd_async.epics.core import (
    epics_signal_r,
    epics_signal_rw,
    epics_signal_rw_rbv,
    epics_signal_x,
)

from dodal.log import LOGGER


@dataclass
class SampleLocation:
    MAX_PUCK = 20
    MAX_POSITION = 22

    puck: int
    position: int

    def __post_init__(self):
        if not (1 <= self.puck <= self.MAX_PUCK or self.puck == -1):
            raise ValueError(
                f"Puck must be between 1 and {self.MAX_PUCK}, got {self.puck}"
            )

        if not (1 <= self.position <= self.MAX_POSITION or self.position == -1):
            raise ValueError(
                f"position must be between 1 and {self.MAX_POSITION}, got {self.position}"
            )


SAMPLE_LOCATION_EMPTY = SampleLocation(-1, -1)


class ProgramNames(StrEnum):
    PUCK = "PUCK.MB6"
    BEAM = "BEAM.MB6"
    SPINNER = "MOTOR.MB6"


class ErrorCodes(IntEnum):
    NO_SAMPLE = 9030
    OK = 0


class ProgramRunning(StrictEnum):
    NO_PROGRAM_RUNNING = "No Program Running"
    PROGRAM_RUNNING = "Program Running"


class SpinnerState(StrictEnum):
    ON = "Spinner On"
    OFF = "Spinner Off"


class CurrentSample(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.puck = epics_signal_rw(int, f"{prefix}PUCK:INDEX")
            self.position = epics_signal_rw(int, f"{prefix}SAMPLE:INDEX")
        super().__init__(name)


class MockRobot(DeviceMock["Robot"]):
    async def connect(self, device: "Robot") -> None:
        def set_program(name: str, *_, **__):
            set_mock_value(device.program_name, name)

        callback_on_mock_put(
            device.puck_load_program, partial(set_program, ProgramNames.PUCK.value)
        )
        callback_on_mock_put(
            device.beam_load_program, partial(set_program, ProgramNames.BEAM.value)
        )

        callback_on_mock_put(
            device._spinner_load_program,  # noqa: SLF001
            partial(set_program, ProgramNames.SPINNER.value),
        )

        def program_running(*_, **__):
            async def _program_running():
                set_mock_value(device.program_running, ProgramRunning.PROGRAM_RUNNING)
                await asyncio.sleep(0.01)
                set_mock_value(
                    device.program_running, ProgramRunning.NO_PROGRAM_RUNNING
                )

            asyncio.create_task(_program_running())

        callback_on_mock_put(device.puck_pick, program_running)
        callback_on_mock_put(device.puck_place, program_running)

        callback_on_mock_put(device.beam_place, program_running)
        callback_on_mock_put(device.beam_pick, program_running)

        callback_on_mock_put(device._spinner_off, program_running)  # noqa: SLF001
        callback_on_mock_put(device._spinner_on, program_running)  # noqa: SLF001


@default_mock_class(MockRobot)
class Robot(StandardReadable, Movable[SampleLocation]):
    """The sample changing robot."""

    # How long to wait for the robot
    PROGRAM_LOADED_TIMEOUT = 1.0
    PROGRAM_STARTED_RUNNING_TIMEOUT = 10.0
    PROGRAM_COMPLETED_TIMEOUT = 60.0

    def __init__(self, robot_prefix: str, current_sample_prefix: str, name: str = ""):
        with self.add_children_as_readables():
            # Any signals that should be read at every point in the scan
            self.puck_sel = epics_signal_rw_rbv(float, f"{robot_prefix}PUCK:PUCK_SEL")
            self.pos_sel = epics_signal_rw_rbv(float, f"{robot_prefix}PUCK:POS_SEL")

        self.current_sample = CurrentSample(current_sample_prefix)

        self.program_name = epics_signal_rw(str, f"{robot_prefix}PROGRAM_NAME")

        self.program_running = epics_signal_r(
            ProgramRunning, f"{robot_prefix}PROGRAM_RUNNING"
        )

        self.program_err_code = epics_signal_r(float, f"{robot_prefix}PRG_ERR_CODE")
        self.program_err_message = epics_signal_r(str, f"{robot_prefix}RUN_ERR_MSG")

        self.run_err_code = epics_signal_r(float, f"{robot_prefix}RUN_ERR_CODE")
        self.controller_err_code = epics_signal_r(float, f"{robot_prefix}CNTL_ERR_CODE")

        self.program_line = epics_signal_r(
            Sequence[str], f"{robot_prefix}LINE_CONTENTS"
        )
        self.controller_err_message = epics_signal_r(
            Sequence[str], f"{robot_prefix}CNTL_ERR_MSG"
        )

        self._spinner_rbv = epics_signal_r(SpinnerState, f"{robot_prefix}SPINNER_STATE")
        self._spinner_off = epics_signal_x(f"{robot_prefix}MOTOR:ACTION0.PROC")
        self._spinner_on = epics_signal_x(f"{robot_prefix}MOTOR:ACTION1.PROC")
        self._spinner_load_program = epics_signal_x(f"{robot_prefix}MOTOR:LOAD.PROC")

        self.spinner = derived_signal_rw(
            self._get_spinner_state, self._set_spinner_state, rbv=self._spinner_rbv
        )

        self.puck_pick = epics_signal_x(f"{robot_prefix}PUCK:ACTION0.PROC")
        self.puck_place = epics_signal_x(f"{robot_prefix}PUCK:ACTION1.PROC")
        self.puck_load_program = epics_signal_x(f"{robot_prefix}PUCK:LOAD.PROC")

        self.beam_pick = epics_signal_x(f"{robot_prefix}BEAM:ACTION0.PROC")
        self.beam_place = epics_signal_x(f"{robot_prefix}BEAM:ACTION1.PROC")
        self.beam_load_program = epics_signal_x(f"{robot_prefix}BEAM:LOAD.PROC")

        self.servo_off = epics_signal_x(f"{robot_prefix}SOFF.PROC")
        self.servo_on = epics_signal_x(f"{robot_prefix}SON.PROC")

        self.reset = epics_signal_x(f"{robot_prefix}RESET.PROC")

        self.home = epics_signal_x(f"{robot_prefix}Home.PROC")

        super().__init__(name)

    async def _trigger_program_and_wait_for_complete(self, trigger_signal: SignalX):
        await trigger_signal.trigger()

        await wait_for_value(
            self.program_running,
            ProgramRunning.PROGRAM_RUNNING,
            timeout=self.PROGRAM_STARTED_RUNNING_TIMEOUT,
        )
        await wait_for_value(
            self.program_running,
            ProgramRunning.NO_PROGRAM_RUNNING,
            timeout=self.PROGRAM_COMPLETED_TIMEOUT,
        )

    async def _load_program_and_wait_for_loaded(
        self, trigger_signal: SignalX, program_name: ProgramNames
    ):
        await trigger_signal.trigger()

        await wait_for_value(
            self.program_name, program_name.value, timeout=self.PROGRAM_LOADED_TIMEOUT
        )

    async def _load(self, location: SampleLocation):
        await self._set_spinner_state(SpinnerState.OFF)

        await self._load_program_and_wait_for_loaded(
            self.puck_load_program, ProgramNames.PUCK
        )

        await asyncio.gather(
            set_and_wait_for_value(self.puck_sel, location.puck),
            set_and_wait_for_value(self.pos_sel, location.position),
        )

        await self._trigger_program_and_wait_for_complete(self.puck_pick)

        if (
            int(await self.controller_err_code.get_value())
            == ErrorCodes.NO_SAMPLE.value
        ):
            raise ValueError(
                f"Robot load failed, no sample found at puck {location.puck}, position {location.position}"
            )

        await self._load_program_and_wait_for_loaded(
            self.beam_load_program, ProgramNames.BEAM
        )

        await self._trigger_program_and_wait_for_complete(self.beam_place)

        await asyncio.gather(
            self.current_sample.puck.set(location.puck),
            self.current_sample.position.set(location.position),
        )

    async def _unload(self):
        await self._set_spinner_state(SpinnerState.OFF)

        await self._load_program_and_wait_for_loaded(
            self.beam_load_program, ProgramNames.BEAM
        )

        await self._trigger_program_and_wait_for_complete(self.beam_pick)

        await self._load_program_and_wait_for_loaded(
            self.puck_load_program, ProgramNames.PUCK
        )

        current_puck = await self.current_sample.puck.get_value()
        current_position = await self.current_sample.position.get_value()

        await asyncio.gather(
            set_and_wait_for_value(self.puck_sel, current_puck),
            set_and_wait_for_value(self.pos_sel, current_position),
        )

        await self._trigger_program_and_wait_for_complete(self.puck_place)

        await asyncio.gather(
            self.current_sample.puck.set(0),
            self.current_sample.position.set(0),
        )

    async def _set_spinner_state(self, new_state: SpinnerState) -> None:
        current_spinner_state = await self._spinner_rbv.get_value()
        if new_state == current_spinner_state:
            LOGGER.info(f"Spinner is already {new_state}, doing nothing")
            return

        await self._load_program_and_wait_for_loaded(
            self._spinner_load_program, ProgramNames.SPINNER
        )

        signal_to_set = (
            self._spinner_off if new_state == SpinnerState.OFF else self._spinner_on
        )

        await self._trigger_program_and_wait_for_complete(signal_to_set)

    def _get_spinner_state(self, rbv: SpinnerState) -> SpinnerState:
        # This function is needed so that the derived signal picks up the type hints
        return rbv

    @AsyncStatus.wrap
    async def set(self, value: SampleLocation):
        """Perform a sample load from the specified sample location or a sample unload
        if SAMPLE_LOCATION_EMPTY is specified.

        Args:
            value (SampleLocation): the sample location to load to or
                                    SAMPLE_LOCATION_EMPTY to unload
        """
        if value == SAMPLE_LOCATION_EMPTY:
            await self._unload()
        else:
            await self._load(value)
