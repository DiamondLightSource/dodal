from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    DeviceMock,
    StandardReadable,
    StandardReadableFormat,
    callback_on_mock_put,
    default_mock_class,
    set_mock_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_w
from ophyd_async.epics.motor import Motor

from dodal.devices.motors import _OMEGA, XYZStage


class InstantVirtualAxisMock(DeviceMock["VirtualAxis"]):
    """Mock behaviour that instantly moves readback to setpoint."""

    async def connect(self, device: "VirtualAxis") -> None:
        # When setpoint is written to, immediately update readback and cast to int.
        def _instant_move(value: float, wait: bool):
            set_mock_value(device.user_readback, int(value))

        callback_on_mock_put(device.user_setpoint, _instant_move)


@default_mock_class(InstantVirtualAxisMock)
class VirtualAxis(StandardReadable, Movable[float]):
    """Device that has different user_readback and user_setpoint signals for read and
    write. Represents the virtual axis coordinate system for the
    B07SampleManipulator52B. The user_readback signal is the read signal for this device,
    same as a Motor.
    """

    def __init__(self, pv: str, name: str = ""):
        self.user_setpoint = epics_signal_w(float, pv)
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.user_readback = epics_signal_r(int, pv + ".RBV")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.user_setpoint.set(value)

    def set_name(self, name: str, *, child_name_separator: str | None = None) -> None:
        super().set_name(name, child_name_separator=child_name_separator)
        # Readback should be named the same as its parent in read()
        self.user_readback.set_name(name)


class B07SampleManipulator52B(XYZStage):
    """Sample Manipulator of several Motors and VirtaulAxis.

    Attributes:
        x (Motor): Controls x direction.
        y (Motor): Controls y direction.
        z (Motor): Controls z direction.
        roty (Motor): Controls y rotation.
        rotz (Motor): Controls z rotation.
        xp (Motor): Compound motor for x.
        yp (Motor): Compound motor for y.
        zp (Motor): Compound motor for z.
        omega (VirtualAxis): Virtal rotational axis for the x direction.
        phi (VirtualAxis): Virtal rotational axis for the y direction.
        kappa (VirtualAxis): Virtal rotational axis for the z direction.
    """

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
