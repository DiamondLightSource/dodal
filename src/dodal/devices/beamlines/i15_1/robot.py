import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from functools import partial

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    DeviceMock,
    StandardReadable,
    StrictEnum,
    callback_on_mock_put,
    default_mock_class,
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


@dataclass
class SampleLocation:
    puck: int
    position: int


class ProgramRunning(StrictEnum):
    NO_PROGRAM_RUNNING = "No Program Running"
    PROGRAM_RUNNING = "Program Running"


class CurrentSample(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.puck = epics_signal_rw(int, f"{prefix}PUCK:INDEX")
            self.position = epics_signal_rw(int, f"{prefix}SAMPLE:INDEX")
        super().__init__(name)


class MockRobot(DeviceMock["Robot"]):
    async def connect(self, device: "Robot") -> None:
        def set_program(name, *_, **__):
            set_mock_value(device.program_name, name)

        callback_on_mock_put(device.puck_load_program, partial(set_program, "PUCK.MB6"))
        callback_on_mock_put(device.beam_load_program, partial(set_program, "BEAM.MB6"))

        def program_running(*_, **__):
            async def _program_running():
                set_mock_value(device.program_running, ProgramRunning.PROGRAM_RUNNING)
                await asyncio.sleep(0.01)
                set_mock_value(
                    device.program_running, ProgramRunning.NO_PROGRAM_RUNNING
                )

            asyncio.create_task(_program_running())

        callback_on_mock_put(device.puck_pick, program_running)
        callback_on_mock_put(device.beam_place, program_running)


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

        self.puck_pick = epics_signal_x(f"{robot_prefix}PUCK:ACTION0.PROC")
        self.puck_place = epics_signal_x(f"{robot_prefix}PUCK:ACTION1.PROC")
        self.puck_load_program = epics_signal_x(f"{robot_prefix}PUCK:LOAD.PROC")

        self.beam_pick = epics_signal_x(f"{robot_prefix}BEAM:ACTION0.PROC")
        self.beam_place = epics_signal_x(f"{robot_prefix}BEAM:ACTION1.PROC")
        self.beam_load_program = epics_signal_x(f"{robot_prefix}BEAM:LOAD.PROC")

        self.spinner_pick = epics_signal_x(f"{robot_prefix}MOTOR:ACTION0.PROC")
        self.spinner_place = epics_signal_x(f"{robot_prefix}MOTOR:ACTION1.PROC")
        self.spinner_load_program = epics_signal_x(f"{robot_prefix}MOTOR:LOAD.PROC")

        self.servo_off = epics_signal_x(f"{robot_prefix}SOFF.PROC")
        self.servo_on = epics_signal_x(f"{robot_prefix}SON.PROC")

        self.reset = epics_signal_x(f"{robot_prefix}RESET.PROC")

        self.home = epics_signal_x(f"{robot_prefix}Home.PROC")

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: SampleLocation):
        """Perform a sample load from the specified sample location.

        Args:
            value (SampleLocation): the sample location
        """
        await self.puck_load_program.trigger()

        await wait_for_value(
            self.program_name, "PUCK.MB6", timeout=self.PROGRAM_LOADED_TIMEOUT
        )

        await asyncio.gather(
            set_and_wait_for_value(self.puck_sel, value.puck),
            set_and_wait_for_value(self.pos_sel, value.position),
        )

        await self.puck_pick.trigger()

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

        await self.beam_load_program.trigger()

        await wait_for_value(
            self.program_name, "BEAM.MB6", timeout=self.PROGRAM_LOADED_TIMEOUT
        )

        await self.beam_place.trigger()

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

        await asyncio.gather(
            self.current_sample.puck.set(value.puck),
            self.current_sample.position.set(value.position),
        )
