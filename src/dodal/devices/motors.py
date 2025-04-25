import asyncio
import math
from enum import StrEnum

from ophyd_async.core import StandardReadable, derived_signal_rw, soft_signal_rw
from ophyd_async.epics.motor import Motor


class Axis(StrEnum):
    X = "X"
    Y = "Y"
    Z = "Z"


class XYZPositioner(StandardReadable):
    """

    Standard ophyd_async xyz motor stage, by combining 3 Motors,
    with added infix for extra flexibliy to allow different axes other than x,y,z.

    Parameters
    ----------
    prefix:
        EPICS PV (Common part up to and including :).
    name:
        name for the stage.
    infix:
        EPICS PV, default is the ("X", "Y", "Z").
    Notes
    -----
    Example usage::
        async with init_devices():
            xyz_stage = XYZPositioner("BLXX-MO-STAGE-XX:")
    Or::
        with init_devices():
            xyz_stage = XYZPositioner("BLXX-MO-STAGE-XX:", infix = ("A", "B", "C"))

    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        infix: tuple[str, str, str] = ("X", "Y", "Z"),
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + infix[0])
            self.y = Motor(prefix + infix[1])
            self.z = Motor(prefix + infix[2])
        super().__init__(name=name)


class SixAxisGonio(XYZPositioner):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        infix: tuple[str, str, str, str, str, str] = (
            "X",
            "Y",
            "Z",
            "KAPPA",
            "PHI",
            "OMEGA",
        ),
    ):
        with self.add_children_as_readables():
            self.kappa = Motor(prefix + infix[3])
            self.phi = Motor(prefix + infix[4])
            self.omega = Motor(prefix + infix[5])

            self.oav_i = derived_signal_rw(
                self._get_i,
                self._set_i,
                x=self.x,
                y=self.y,
                z=self.z,
                omega=self.omega,
            )

            self.oav_j = derived_signal_rw(
                self._get_j,
                self._set_j,
                x=self.x,
                y=self.y,
                z=self.z,
                omega=self.omega,
            )

        super().__init__(name=name, prefix=prefix, infix=infix[0:3])

    def _get_j(self, z: float, y: float, omega: float) -> float:
        z_component = z * math.cos(math.radians(omega))
        y_component = y * math.sin(math.radians(omega))
        return z_component + y_component

    async def _set_j(self, value: float) -> None:
        omega = await self.omega.user_readback.get_value()
        z_component = value * math.cos(math.radians(omega))
        y_component = value * math.sin(math.radians(omega))
        await asyncio.gather(
            self.y.set(y_component),
            self.z.set(z_component),
            self.omega.set(omega),
        )

    def _get_i(self, x: float) -> float:
        return x

    async def _set_i(self, value: float) -> None:
        await self.x.set(value)
