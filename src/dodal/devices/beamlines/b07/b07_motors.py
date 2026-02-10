from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.epics.core import epics_signal_r, epics_signal_w
from ophyd_async.epics.motor import Motor

from dodal.devices.motors import _OMEGA, XYZStage


class VirtualAxis(StandardReadable, Movable[float]):
    def __init__(self, pv: str, name: str = ""):
        with self.add_children_as_readables():
            self.user_setpoint = epics_signal_w(float, pv)
            self.user_readback = epics_signal_r(int, pv + ".RBV")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.user_setpoint.set(value)


class B07SampleManipulator52B(XYZStage):
    def __init__(
        self,
        prefix: str,
        x_infix: str = "XP",
        y_infix: str = "YP",
        z_infix: str = "ZP",
        roty: str = "ROTY",
        rotz: str = "ROTZ",
        kappa_infix: str = "KAPPA",
        phi_infix: str = "PHI",
        omega_infix: str = _OMEGA,
        name: str = "",
    ):
        with self.add_children_as_readables():
            # Compound motors
            self.xp = Motor(prefix + x_infix)
            self.yp = Motor(prefix + y_infix)
            self.zp = Motor(prefix + z_infix)

            # Raw motors
            self.roty = Motor(prefix + roty)
            self.rotz = Motor(prefix + rotz)

            # Not standard motors, virtual axes coordinate system.
            self.kappa = VirtualAxis(prefix + kappa_infix)
            self.phi = VirtualAxis(prefix + phi_infix)
            self.omega = VirtualAxis(prefix + omega_infix)

        super().__init__(
            prefix=prefix,
            x_infix=x_infix,
            y_infix=y_infix,
            z_infix=z_infix,
            name=name,
        )
