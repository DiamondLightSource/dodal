import asyncio

from bluesky.protocols import Movable
from ophyd_async.core import DeviceVector
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.i16.utils import MECA_500, kinematics


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

        self.jv = epics_signal_rw(float, f"{prefix}JOINTVEL:SET")

        self.busy = epics_signal_rw(int, f"{prefix}ROBOT:STATUS:BUSY")

        self.motor_offsets = [0, 0, 0, 0, 0, 0]

        self.move_joints_array = epics_signal_rw(
            bool, f"{prefix}PREPARE_MOVE_JOINTS_ARRAY.PROC"
        )

        self.eom = epics_signal_r(float, f"{prefix}ROBOT:STATUS:EOM")

        self.abort = epics_signal_rw(int, f"{prefix}MOTION:ABORT")
        self.resume = epics_signal_rw(int, f"{prefix}MOTION:ABORT")

        self.kinematic_model = kinematics(MECA_500)

        self.x = epics_signal_rw(float, f"{prefix}POSE:X:RBV", f"{prefix}POSE:X:SP")
        self.y = epics_signal_rw(float, f"{prefix}POSE:Y:RBV", f"{prefix}POSE:Y:SP")
        self.z = epics_signal_rw(float, f"{prefix}POSE:Z:RBV", f"{prefix}POSE:Z:SP")

        self.alpha = epics_signal_rw(
            float, f"{prefix}POSE:ALPHA:RBV", f"{prefix}POSE:ALPHA:SP"
        )
        self.beta = epics_signal_rw(
            float, f"{prefix}POSE:BETA:RBV", f"{prefix}POSE:BETA:SP"
        )
        self.gamma = epics_signal_rw(
            float, f"{prefix}POSE:GAMMA:RBV", f"{prefix}POSE:GAMMA:SP"
        )

        self._pose = self._update_pose()

    def _update_pose(self):
        return {
            "x": self.x.get_value(),
            "y": self.y.get_value(),
            "z": self.z.get_value(),
            "alpha": self.alpha.get_value(),
            "beta": self.beta.get_value(),
            "gamma": self.gamma.get_value(),
        }

    @property
    def pose(self):
        return self._pose

    @pose.setter
    async def pose(self, new_pose: dict):
        if not all(axis in self._pose.keys() for axis in new_pose):
            raise ValueError(
                f"Invalid axis passed as pose. Expected: {self._pose.keys()} Recieved: {new_pose.keys()}"
            )

        move_pose = {
            axis: (new_pose[axis] if axis in new_pose else value)
            for axis, value in self._pose.items()
        }
        await self.asynchronousMoveToXYZ(move_pose)
        self._pose = self._update_pose()

    async def setSpeed(self, speed):
        """Speed is set as a percentage. 10 is a good value"""
        self.jv.set(speed)

    async def asynchronousMoveToJoints(self, values):
        self.busy.set(1, wait=True)

        for i in range(len(self.joints)):
            self.joints[i].set(values[i] + self.motor_offsets[i])

        self.move_joints_array.set(True)

    async def asynchronousMoveToXYZ(self, values: dict):
        _x, _y, _z = values["x"], values["y"], values["z"]
        r_alpha, r_beta, r_gamma = values["alpha"], values["beta"], values["gamma"]
        motor_values = self.kinematic_model.setEulerTarget(
            [_x, _y, _z], r_alpha, r_beta, r_gamma
        )
        await self.asynchronousMoveToJoints(motor_values)

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
