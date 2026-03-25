from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_rw_rbv
from ophyd_async.epics.motor import Motor

from dodal.devices.motors import _OMEGA, XYZStage


class VirtualAxis(StandardReadable, Movable[float]):
    """Represents the virtual axis coordinate system for the B07SampleManipulator52B.
    The value signal is the read signal for this device.
    """

    def __init__(self, pv: str, name: str = ""):
        """Initialise the device via pv and name configuration.

        Args:
            pv (str): The base PV to connect to the virtual axis.
            name (str, optional): Name of this device.
        """
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.value = epics_signal_rw_rbv(float, pv, read_suffix=":RBV")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.value.set(value)

    def set_name(self, name: str, *, child_name_separator: str | None = None) -> None:
        super().set_name(name, child_name_separator=child_name_separator)
        # Value should be named the same as its parent in read()
        self.value.set_name(name)


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
        roty_infix: str = "ROTY",
        rotz_infix: str = "ROTZ",
        kappa_infix: str = "KAPPA",
        phi_infix: str = "PHI",
        omega_infix: str = _OMEGA,
        name: str = "",
    ):
        """Initialise the device via prefix and infix PV configuration.

        Args:
            prefix (str): Base PV used for connecting signals.
            x_infix (str, optional): Infix between base prefix and x motor record.
            y_infix (str, optional): Infix between base prefix and y motor record.
            z_infix (str, optional): Infix between base prefix and z motor record.
            roty_infix (str, optional): Infix between base prefix and roty motor record.
            rotz_infix (str, optional): Infix between base prefix and rotz motor record.
            kappa_infix (str, optional): Infix between base prefix and kappa virtual axis.
            phi_infix (str, optional): Infix between base prefix and phi virtual axis.
            omega_infix (str, optional): Infix between base prefix and omega virtual axis.
            name (str, optional): The name of this device.
        """
        with self.add_children_as_readables():
            # Compound motors
            self.xp = Motor(prefix + x_infix)
            self.yp = Motor(prefix + y_infix)
            self.zp = Motor(prefix + z_infix)

            # Raw motors
            self.roty = Motor(prefix + roty_infix)
            self.rotz = Motor(prefix + rotz_infix)

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
