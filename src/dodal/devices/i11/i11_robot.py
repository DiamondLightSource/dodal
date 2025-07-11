import time
from typing import Annotated as A

from bluesky.protocols import Locatable, Location
from ophyd_async.core import AsyncStatus, SignalRW, StandardReadable
from ophyd_async.epics.core import PvSuffix, epics_signal_x

from dodal.log import Logger

# class RobotJobs(StrictEnum):

# class RobotSampleState(StrictEnum):
#     CAROSEL = "on carousel"


class I11Robot(StandardReadable, Locatable):
    def __init__(self, prefix: str, name=""):
        self.start = epics_signal_x(prefix + "START.VAL")
        self.hold = epics_signal_x(prefix + "HOLD.VAL")
        self.job = epics_signal_x(prefix + "JOB.VAL")
        self.svon = epics_signal_x(prefix + "SVON.VAL")
        self.err = epics_signal_x(prefix + "ERR.VAL")

        # self.robot_plc_check = "BL11I-MO-STEP-19:PLCSTATUS_OK"
        # self.robot_feedrate_check = "BL11I-MO-STEP-19:FEEDRATE"
        # self.robot_feedrate_limit = "BL11I-MO-STEP-19:FEEDRATE_LIMIT"

        self.robot_sample_state: A[SignalRW[int], PvSuffix.rbv("D010")]
        self.next_sample_position: A[SignalRW[int], PvSuffix.rbv("D011")]
        self.current_sample_position: A[SignalRW[int], PvSuffix.rbv("D012")]
        self.door_latch_state = A[SignalRW[int], PvSuffix.rbv("NEEDRECOVER")]

        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        pass

    # @AsyncStatus.wrap
    async def locate(self) -> Location:
        # setpoint readback
        return Location(setpoint=1, readback=1)

    def start():
        start_time = time.time()
        Logger.debug(f"Robot Started: {start_time}")
