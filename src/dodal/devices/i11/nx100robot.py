import asyncio
from enum import Enum

from bluesky.protocols import Locatable, Location, Pausable, Stoppable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StrictEnum,
    set_and_wait_for_value,
)
from ophyd_async.epics.core import epics_signal_rw, epics_signal_rw_rbv, epics_signal_x

from dodal.log import LOGGER


class RobotJobs(StrictEnum):
    RECOVER = "RECOVER"  # Recover from unknown state
    PICK_CAROUSEL = "PICKC"  # Pick a sample from the carousel.
    PLACE_CAROUSEL = "PLACEC"  # Place a sample onto the carousel
    PICK_DIFFRACTOMETER = "PICKD"  # Pick a sample from the diffractometer.
    PLACE_DIFFRACTOMETER = "PLACED"  # Place a sample onto the diffractometer.
    GRIPO = "GRIPO"
    GRIPC = "GRIPC"
    TABLEIN = "TABLEIN"
    TABLEOUT = "TABLEOUT"
    UNLOAD = "UNLOAD"


class RobotSampleState(float, Enum):
    CAROUSEL = 0.0  # Sample is on carousel
    ONGRIP = 1.0  # Sample is on the gripper
    DIFFRACTOMETER = 2.0  # Sample is on the diffractometer
    UNKNOWN = 3.0


class NX100Robot(StandardReadable, Locatable[int], Stoppable, Pausable):
    """
    This is a Yaskawa Motoman that uses an NX100 controller. It consists of a robot arm
    with a gripper and a carousel for sample handling. It can pick and place samples
    from the carousel to the diffractometer and vice versa.

    Has set, pause, resume, stop, locate, stage methods.
    """

    MAX_NUMBER_OF_SAMPLES = 200
    MIN_NUMBER_OF_SAMPLES = 1

    def __init__(self, prefix: str, name: str = ""):
        self.start = epics_signal_x(prefix + "START")
        self.hold = epics_signal_rw(bool, prefix + "HOLD")
        self.job = epics_signal_rw(RobotJobs, prefix + "JOB")
        self.servo_on = epics_signal_rw(bool, prefix + "SVON")  # Servo on/off
        self.err = epics_signal_rw(int, prefix + "ERR")

        self.robot_sample_state = epics_signal_rw(float, prefix + "D010")
        self.next_sample_position = epics_signal_rw_rbv(
            int, prefix + "D011", read_suffix=":RBV"
        )
        self.current_sample_position = epics_signal_rw_rbv(
            int, prefix + "D012", read_suffix=":RBV"
        )
        self.door_latch_state = epics_signal_rw(int, prefix + "NEEDRECOVER")

        super().__init__(name=name)

    async def recover(self):
        await asyncio.gather(
            self.start.trigger(),
            set_and_wait_for_value(self.job, RobotJobs.RECOVER),
            set_and_wait_for_value(self.err, False),
        )

    async def clear_sample(self, table_in: bool = True):
        """clears the sample from the diffractometer and places it on the carousel.
        if table_in is True, it will also move the sample holder to the table in position."""

        sample_state = await self.robot_sample_state.get_value()
        if sample_state == RobotSampleState.DIFFRACTOMETER:
            await asyncio.gather(
                set_and_wait_for_value(self.job, RobotJobs.PICK_DIFFRACTOMETER),
                set_and_wait_for_value(self.job, RobotJobs.PLACE_CAROUSEL),
            )
        elif sample_state == RobotSampleState.ONGRIP:
            await set_and_wait_for_value(self.job, RobotJobs.PLACE_CAROUSEL)
        elif sample_state == RobotSampleState.CAROUSEL:
            pass
        elif sample_state == RobotSampleState.UNKNOWN:
            LOGGER.error("UNKNOWN sample state from robot, exit")
        else:
            raise ValueError(f"Unknown sample state: {sample_state}")

        if table_in:
            await set_and_wait_for_value(self.job, RobotJobs.TABLEIN)

        LOGGER.info("Sample cleared from diffractometer")

    async def load_sample(self, sample_location: int):
        """Loads a sample from the carousel to the diffractometer."""
        sample_state = await self.robot_sample_state.get_value()
        if sample_state == RobotSampleState.CAROUSEL:
            await set_and_wait_for_value(self.job, RobotJobs.PICK_CAROUSEL)
            await set_and_wait_for_value(self.job, RobotJobs.PLACE_DIFFRACTOMETER)
        elif sample_state == RobotSampleState.ONGRIP:
            await set_and_wait_for_value(self.job, RobotJobs.PLACE_DIFFRACTOMETER)
        elif sample_state == RobotSampleState.DIFFRACTOMETER:
            pass
        elif sample_state == RobotSampleState.UNKNOWN:
            LOGGER.warning(f"No sample at sample holder position {sample_location}")
            LOGGER.error("UNKNOWN sample state from robot, exit")
        else:
            raise ValueError(f"Unknown sample state: {sample_state}")

    @AsyncStatus.wrap
    async def set(self, sample_location: int) -> None:
        if (
            sample_location < self.MIN_NUMBER_OF_SAMPLES
            or sample_location > self.MAX_NUMBER_OF_SAMPLES
        ):
            raise ValueError(
                f"Sample location must be between {self.MIN_NUMBER_OF_SAMPLES} and {self.MAX_NUMBER_OF_SAMPLES}, got {sample_location}"
            )
        if await self.current_sample_position.get_value() == sample_location:
            LOGGER.info(f"Robot already at position {sample_location}")
        else:
            await self.clear_sample(table_in=False)
            await self.next_sample_position.set(sample_location, wait=True)
            await self.load_sample(sample_location)
            await self.current_sample_position.set(sample_location)

    async def pause(self):
        await set_and_wait_for_value(self.hold, True)

    async def resume(self):
        await set_and_wait_for_value(self.hold, False)

    async def stop(self, success: bool = True):
        await set_and_wait_for_value(self.hold, True)
        if not success:
            await set_and_wait_for_value(self.hold, False)
            await self.clear_sample()

    @AsyncStatus.wrap
    async def stage(self) -> None:
        """Set up the device for acquisition."""
        await asyncio.gather(
            set_and_wait_for_value(self.servo_on, True),
            set_and_wait_for_value(self.hold, False),
            self.start.trigger(),
        )

    async def locate(self) -> Location[int]:
        location = await self.current_sample_position.locate()
        return location
