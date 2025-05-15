import asyncio
import math
from enum import Enum

from ophyd_async.core import StandardReadable, derived_signal_rw
from ophyd_async.epics.motor import Motor


class Axis(Enum):
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


class FourAxisGonio(XYZPositioner):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        infix: tuple[str, str, str, str] = (
            "X",
            "Y",
            "Z",
            "OMEGA",
        ),
        upward_axis_at_0: Axis = Axis.Y,
        upward_axis_at_minus_90: Axis = Axis.Z,
    ):
        with self.add_children_as_readables():
            self.omega = Motor(prefix + infix[3])

        super().__init__(name=name, prefix=prefix, infix=infix[0:3])

        # Axes corresponding to the co-ordinate axis signals that move the stage
        # upwards when omega = 0 and omega = -90 respectively i.e. vertical and
        # horizontal movement in the rotating frame of reference of the stage
        self._vertical_stage_axis = self._get_axis_signal(upward_axis_at_0)
        self._horizontal_stage_axis = self._get_axis_signal(upward_axis_at_minus_90)

        # i and j in the plane of the OAV
        self.i = derived_signal_rw(self._get_i, self._set_i, x=self.x)
        self.j = derived_signal_rw(
            self._get_j,
            self._set_j,
            vertical_stage_axis=self._vertical_stage_axis,
            horizontal_stage_axis=self._horizontal_stage_axis,
            omega=self.omega,
        )

    def _get_j(
        self, vertical_stage_axis: float, horizontal_stage_axis: float, omega: float
    ) -> float:
        vertical_axis_component = calculate_vertical_j_component(
            vertical_stage_axis, omega
        )
        horizontal_axis_component = calculate_horizontal_j_component(
            horizontal_stage_axis, omega
        )
        return vertical_axis_component + horizontal_axis_component

    async def _set_j(self, value: float) -> None:
        omega = await self.omega.user_readback.get_value()
        vertical_component = calculate_vertical_j_component(value, omega)
        horizontal_component = calculate_horizontal_j_component(value, omega)
        await asyncio.gather(
            self._vertical_stage_axis.set(vertical_component),
            self._horizontal_stage_axis.set(horizontal_component),
            self.omega.set(omega),
        )

    def _get_i(self, x: float) -> float:
        return x

    async def _set_i(self, value: float) -> None:
        await self.x.set(value)

    def _get_axis_signal(self, axis: Axis) -> Motor:
        match axis:
            case Axis.X:
                return self.x
            case Axis.Y:
                return self.y
            case Axis.Z:
                return self.z


class SixAxisGonio(FourAxisGonio):
    """

    Six-axis goniometer with a standard xyz stage and three axes of rotation: kappa, phi
    and omega.

        Parameters
    ----------
    prefix:
        EPICS PV (Common part up to and including :).
    name:
        name for the stage.
    infix:
        EPICS PV, default is the ("X", "Y", "Z", "KAPPA", "PHI", "OMEGA").
    upward_axis_at_0:
        Axis as an enum (Axis.X, Axis.Y or Axis.Z), that points upwards when ω = 0°.
        Default is Axis.Y
    upward_axis_at_minus_90:
        Axis as an enum (Axis.X, Axis.Y or Axis.Z), that points upwards when ω = -90°.
        Default is Axis.Z
    Notes
    -----
    Example usage::
        async with init_devices():
            xyz_stage = XYZPositioner("BLXX-MO-STAGE-XX:")
    Or::
        with init_devices():
            xyz_stage = XYZPositioner("BLXX-MO-STAGE-XX:", infix = ("A", "B", "C", \
            "KAPPA", "PHI", "OMEGA"))

    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        infix: tuple[str, str, str, str, str, str] = (
            "X",
            "Y",
            "Z",
            "OMEGA",
            "KAPPA",
            "PHI",
        ),
        upward_axis_at_0: Axis = Axis.Y,
        upward_axis_at_minus_90: Axis = Axis.Z,
    ):
        with self.add_children_as_readables():
            self.kappa = Motor(prefix + infix[4])
            self.phi = Motor(prefix + infix[5])

        super().__init__(
            name=name,
            prefix=prefix,
            infix=infix[0:4],
            upward_axis_at_0=upward_axis_at_0,
            upward_axis_at_minus_90=upward_axis_at_minus_90,
        )


def calculate_vertical_j_component(length: float, angle: float):
    return length * math.cos(math.radians(angle))


def calculate_horizontal_j_component(length: float, angle: float):
    return length * math.sin(math.radians(angle))
