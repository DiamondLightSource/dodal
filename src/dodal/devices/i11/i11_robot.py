import asyncio

from bluesky.protocols import Locatable, Location
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
    PICKC = "PICKC"  # Pick a sample from the carousel.
    PLACEC = "PLACEC"  # Place a sample onto the carousel
    PICKD = "PICKD"  # Pick a sample from the diffractometer.
    PLACED = "PLACED"  # Place a sample onto the diffractometer.
    GRIPO = "GRIPO"
    GRIPC = "GRIPC"
    TABLEIN = "TABLEIN"
    TABLEOUT = "TABLEOUT"
    UNLOAD = "UNLOAD"


class RobotSampleState:
    CAROSEL = 0.0
    ONGRIP = 1.0
    DIFF = 2.0
    UNKNOWN = 3.0


class I11Robot(StandardReadable, Locatable):
    # TODO: Test this

    """

    This is a Yaskawa Motoman that uses an NX100 controller

    The following PV's are related to the robot and may be needed for some functionality
    self.robot_plc_check = "BL11I-MO-STEP-19:PLCSTATUS_OK"
    self.robot_feedrate_check = "BL11I-MO-STEP-19:FEEDRATE"
    self.robot_feedrate_limit = "BL11I-MO-STEP-19:FEEDRATE_LIMIT"
    """

    MAX_ROBOT_NEXT_POSITION_ATTEMPTS = 3
    MAX_NUMBER_OF_SAMPLES = 200
    MIN_NUMBER_OF_SAMPLES = 1
    LOAD_TIMEOUT = 300

    def __init__(self, prefix: str, name=""):
        self.start = epics_signal_x(prefix + "START")
        self.hold = epics_signal_x(prefix + "HOLD")
        self.job = epics_signal_rw(RobotJobs, prefix + "JOB")
        self.servo_on = epics_signal_x(prefix + "SVON")  # Servo on/off
        self.err = epics_signal_x(prefix + "ERR")

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
        await set_and_wait_for_value(self.job, RobotJobs.RECOVER)

    async def clear_sample(self, table_in=True):
        sample_state = await self.robot_sample_state.get_value()
        if sample_state == RobotSampleState.DIFF:
            await asyncio.gather(
                set_and_wait_for_value(self.job, RobotJobs.PICKD),
                set_and_wait_for_value(self.job, RobotJobs.PLACEC),
            )
        elif sample_state == RobotSampleState.ONGRIP:
            await set_and_wait_for_value(self.job, RobotJobs.PLACEC)
        elif sample_state == RobotSampleState.CAROSEL:
            pass
        elif sample_state == RobotSampleState.UNKNOWN:
            LOGGER.error("UNKNOWN sample state from robot, exit")
        else:
            raise Exception

        if table_in:
            await set_and_wait_for_value(self.job, RobotJobs.TABLEIN)

        LOGGER.info("Sample cleared from diffractometer")

    async def load_sample(self, sample_location: int):
        attempts = 0
        success = False

        while (attempts < self.MAX_ROBOT_NEXT_POSITION_ATTEMPTS) and (not success):
            attempts += 1
            # poll sample state before changing sample as event update not
            # reliable anymore.
            sample_state = await self.robot_sample_state.get_value()
            # clear sample from diffractometer before putting on next sample
            await self.clear_sample(table_in=False)

            if sample_state == RobotSampleState.CAROSEL:
                await self.set(sample_location)
                await set_and_wait_for_value(self.job, RobotJobs.PICKC)

                if sample_state == RobotSampleState.ONGRIP:
                    await set_and_wait_for_value(self.job, RobotJobs.PLACED)
                    success = True
                else:
                    await set_and_wait_for_value(self.job, RobotJobs.TABLEIN)
                    LOGGER.warning(
                        f"No sample at sample golder position {sample_location}"
                    )
                    LOGGER.warning(
                        f"Attempt {attempts} of {self.MAX_ROBOT_NEXT_POSITION_ATTEMPTS}"
                    )

        if not success:
            LOGGER.warning(
                f"Still no sample at sample holder position {sample_location} after {attempts} attempts"
            )

    @AsyncStatus.wrap
    async def set(self, value: int) -> None:
        if await self.current_sample_position.get_value() == value:
            LOGGER.info(f"Robot already at position {value}")
        else:
            await self.next_sample_position.set(value=value)

    # @AsyncStatus.wrap
    async def locate(self) -> Location:
        # setpoint readback
        location = await self.current_sample_position.locate()
        return location
