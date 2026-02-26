from typing import Annotated

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_rw_rbv
from ophyd_async.epics.motor import Motor

from dodal.devices.motors import _OMEGA, DefaultInfix, XYZStage


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

    roty: Annotated[Motor, DefaultInfix("ROTY")]
    rotz: Annotated[Motor, DefaultInfix("ROTZ")]
    xp: Annotated[Motor, DefaultInfix("XP")]
    yp: Annotated[Motor, DefaultInfix("YP")]
    zp: Annotated[Motor, DefaultInfix("ZP")]

    def __init__(
        self,
        prefix: str,
        kappa_infix: str = "KAPPA",
        phi_infix: str = "PHI",
        omega_infix: str = _OMEGA,
        name: str = "",
        **motor_infix_overrides: str,
    ):
        """Initialise the device via prefix and infix PV configuration."""
        with self.add_children_as_readables():
            # Not standard motors, virtual axes coordinate system.
            self.kappa = VirtualAxis(prefix + kappa_infix)
            self.phi = VirtualAxis(prefix + phi_infix)
            self.omega = VirtualAxis(prefix + omega_infix)

        super().__init__(
            prefix=prefix,
            name=name,
            **motor_infix_overrides,
        )
