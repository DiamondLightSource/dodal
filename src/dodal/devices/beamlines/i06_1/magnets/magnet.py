import asyncio
import math
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    derived_signal_r,
    soft_signal_rw,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_x


class MagnetModes(StrictEnum):
    UNIAXIAL_X = "UNIAXIAL_X"
    UNIAXIAL_Y = "UNIAXIAL_Y"
    UNIAXIAL_Z = "UNIAXIAL_Z"
    SPHERICAL = "SPHERICAL"
    PLANAR_XZ = "PLANAR_XZ"
    QUADRANT_XY = "QUADRANT_XY"
    CUBIC = "CUBIC"
    UNDEFINED = "UNDEFINED"


class MagnetRampStatus(StrictEnum):
    RAMPING = "RAMPING"
    RAMP_MADE = "RAMP MADE"


class MagnetLimitStatus(StrictEnum):
    VIOLTATION = "VIOLATION"
    OK = "OK"


def read_theta(x: float, z: float) -> float:
    theta = math.degrees(math.atan2(-x, z))
    return theta % 360


def read_rho(x: float, y: float, z: float) -> float:
    return math.hypot(x, y, z)


def read_phi(x: float, y: float, z: float) -> float:
    return math.degrees(math.atan2(math.hypot(x, z), y))


@dataclass
class MagnetPosition:
    x: float
    y: float
    z: float

    def to_spherical(self) -> "SphericalMagnetPosition":
        return SphericalMagnetPosition(
            rho=read_rho(self.x, self.y, self.z),
            theta=read_theta(self.x, self.z),
            phi=read_phi(self.x, self.y, self.z),
        )


@dataclass(frozen=True)
class SphericalMagnetPosition:
    rho: float
    theta: float  # degrees
    phi: float  # degrees

    def to_cartesian(self) -> MagnetPosition:
        theta = math.radians(self.theta)
        phi = math.radians(self.phi)

        return MagnetPosition(
            x=-self.rho * math.sin(phi) * math.sin(theta),
            y=self.rho * math.cos(phi),
            z=self.rho * math.sin(phi) * math.cos(theta),
        )


class RampMagnetController(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.out = epics_signal_rw(float, prefix + "STS:RAMPRATE:TPM")
        self.in_ = epics_signal_rw(float, prefix + "SET:DMD:RAMPRATE:TPM")
        self.limit = epics_signal_rw(float, prefix + "LIM:RAMPRATE:TPM")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.in_.set(value)


class RampMagnetControllerGroup(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.x = RampMagnetController(prefix + "-01:")
            self.y = RampMagnetController(prefix + "-02:")
            self.z = RampMagnetController(prefix + "-03:")

        super().__init__(name)


# ToDo - Use StandardMovable?
class MagnetAxis(StandardReadable, Movable[float]):
    def __init__(
        self,
        prefix: str,
        axis: str,
        ramp_controller: RampMagnetController,
        magnet_set_within_boundary: Callable[[], Awaitable[None]],
        name: str = "",
    ):
        # Used in fastfieldscan, need to add fly scan logic.
        self.ramp_controller_ref = Reference(ramp_controller)

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.readback = epics_signal_r(float, prefix + "RBV")

        self.demand = epics_signal_rw(float, prefix + "DMD")

        self._axis = axis
        self._magnet_set_within_boundary = magnet_set_within_boundary

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        values = {self._axis: value}
        await self._magnet_set_within_boundary(**values)


# Add support for GDA SuperconductingMagnetControllerClass as well
class SuperConductingMagnet(StandardReadable, Movable[MagnetPosition]):
    def __init__(
        self, prefix: str, ramp_controllers: RampMagnetControllerGroup, name: str = ""
    ):
        with self.add_children_as_readables():
            # Cartesian and real pv values
            self.x = MagnetAxis(
                prefix + "X:", "x", ramp_controllers.x, self.set_within_boundary
            )
            self.y = MagnetAxis(
                prefix + "Y:", "y", ramp_controllers.y, self.set_within_boundary
            )
            self.z = MagnetAxis(
                prefix + "Z:", "z", ramp_controllers.y, self.set_within_boundary
            )

            # Spherical representations of x, y, z
            self.theta = derived_signal_r(
                read_theta, x=self.x.readback, z=self.z.readback
            )
            self.rho = derived_signal_r(
                read_rho, x=self.x.readback, y=self.y.readback, z=self.z.readback
            )
            self.phi = derived_signal_r(
                read_phi, x=self.x.readback, y=self.y.readback, z=self.z.readback
            )

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.mode = epics_signal_rw(MagnetModes, prefix + "MODE")
            self.timeout = soft_signal_rw(float, initial_value=300)
            self.delay = soft_signal_rw(float, initial_value=0.1)

        self.ramp_status = epics_signal_rw(MagnetRampStatus, prefix + "RAMPSTATUS")

        self.limit_status = epics_signal_rw(MagnetLimitStatus, prefix + "LIMITSTATUS")
        self.start_ramp = epics_signal_x(prefix + "STARTRAMP.PROC")

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: MagnetPosition | SphericalMagnetPosition):
        if isinstance(value, SphericalMagnetPosition):
            value = value.to_cartesian()
        await self.set_within_boundary(x=value.x, y=value.y, z=value.z)

    async def _ramp(self):
        # ToDo - Use TimeoutCalculated from ophyd-async in new release.
        timeout = await self.timeout.get_value()
        await self.start_ramp.trigger(timeout=timeout)
        await wait_for_value(self.ramp_status, MagnetRampStatus.RAMP_MADE, timeout)

        if await self.limit_status.get_value() == MagnetLimitStatus.VIOLTATION:
            raise RuntimeError(
                f"{self.limit_status.name} is at position {MagnetLimitStatus.VIOLTATION}"
            )

    async def set_within_boundary(
        self, x: float | None = None, y: float | None = None, z: float | None = None
    ):
        """Move magnet while ensuring field magnitude never increases before decreases
        have completed.
        """
        if x is None and y is None and z is None:
            raise RuntimeError("Args x, y, and z cannot all be None at the same time.")

        # For keeping the magnitude constrained to avoid quench, always do the decreasing before increasing motors
        # Can this be simplified?
        x0, y0, z0 = await asyncio.gather(
            self.x.readback.get_value(),
            self.y.readback.get_value(),
            self.z.readback.get_value(),
        )
        x = x0 if x is None else x
        y = y0 if y is None else y
        z = z0 if z is None else z

        dx = abs(x) - abs(x0)
        dy = abs(y) - abs(y0)
        dz = abs(z) - abs(z0)

        # Decrease Z first
        if dz < 0:
            await self.z.demand.set(z)
            await self._ramp()
        # Then decrease X
        if dx < 0:
            await self.x.demand.set(x)
            await self._ramp()
        # Then decrease Y
        if dy < 0:
            await self.y.demand.set(y)
            await self._ramp()
        # Finally perform all increases together
        if dx > 0 or dy > 0 or dz > 0:
            await asyncio.gather(
                self.x.demand.set(x),
                self.y.demand.set(y),
                self.z.demand.set(z),
            )
            await self._ramp()
