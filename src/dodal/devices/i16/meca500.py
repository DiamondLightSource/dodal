import asyncio

from bluesky.protocols import Movable
from ophyd_async.core import DeviceVector
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class meca500(Movable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.joints = DeviceVector(
            {
                i: epics_signal_rw(float, f"{prefix}JOINTS:THETA{i + 1}:SP")
                for i in range(6)
            }
        )

        self.joints_rbv = DeviceVector(
            {
                i: epics_signal_rw(float, f"{prefix}JOINTS:THETA{i + 1}:RBV")
                for i in range(6)
            }
        )

        self.jv = epics_signal_rw(float, prefix + "JOINTVEL:SET")

        self.busy = epics_signal_rw(int, prefix + "ROBOT:STATUS:BUSY")

        self.motor_offsets = [0, 0, 0, 0, 0, 0]

        self.move_joints_array = epics_signal_rw(
            bool, prefix + "PREPARE_MOVE_JOINTS_ARRAY.PROC"
        )

        self.eom = epics_signal_r(float, prefix + "ROBOT:STATUS:EOM")

        self.abort = epics_signal_rw(int, prefix + "MOTION:ABORT")
        self.resume = epics_signal_rw(int, prefix + "MOTION:ABORT")

    async def setSpeed(self, speed):
        """Speed is set as a percentage. 10 is a good value"""
        self.jv.set(speed)

    async def asynchronousMoveTo(self, values):
        self.busy.set(1, wait=True)

        for i in range(len(self.joints)):
            self.joints[i].set(values[i] + self.motor_offsets[i])

        self.move_joints_array.set(True)

    async def getPosition(self):
        arm = [
            (await self.joints_rbv[i].get_value() - self.motor_offsets[i])
            for i in range(len(self.joints_rbv))
        ]

        return list(arm)

    async def isBusy(self):
        loopcheck = 0
        while (
            await self.eom.get_value() == "0.0"
            and await self.busy.get_value() == 1
            and loopcheck < 10
        ):
            loopcheck += 1
            await asyncio.sleep(0.1)

        if await self.eom.get_value() == "0.0":
            self.busy.set(0)
            return False

        return True

    def stop(self):
        self.abort.set(1)
        self.resume.set(1)
        self.busy.set(1)
