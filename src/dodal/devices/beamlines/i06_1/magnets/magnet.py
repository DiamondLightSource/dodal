import asyncio
import math
from dataclasses import dataclass

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    SignalRW,
    StandardReadable,
    StrictEnum,
    derived_signal_r,
    soft_signal_rw,
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


@dataclass
class MagnetPosition:
    x: float
    y: float
    z: float


# class SphericalCoorindates(StandardReadable):

#     def __init__(self, x: SignalR[float], y: SignalR[float], z: SignalR[float]):
#         self.theta =


def read_theta(x: float, z: float) -> float:
    theta = math.degrees(math.atan2(-x, z))
    return theta % 360


def read_rho(x: float, y: float, z: float) -> float:
    return math.hypot(x, y, z)


def read_phi(x: float, y: float, z: float) -> float:
    return math.degrees(math.atan2(math.hypot(x, z), y))


def write_x(rho: float, theta: float, phi: float, x: SignalRW[float]) -> float:
    theta = math.radians(theta)
    phi = math.radians(phi)
    x.set(-rho * math.sin(phi) * math.sin(theta))


def write_y(rho: float, theta: float, phi: float) -> float:
    phi = math.radians(phi)
    return rho * math.cos(phi)


def write_z(rho: float, theta: float, phi: float) -> float:
    theta = math.radians(theta)
    phi = math.radians(phi)
    return rho * math.sin(phi) * math.cos(theta)


# Need to add spherical and cartesian coordinates
class SuperConductingMagnet(StandardReadable, Movable[MagnetPosition]):
    def __init__(self, prefix: str, name: str = ""):

        # Demand values
        self.xi = epics_signal_rw(float, prefix + "X:DMD")
        self.yi = epics_signal_rw(float, prefix + "X:DMD")
        self.zi = epics_signal_rw(float, prefix + "X:DMD")

        # Readback values
        self.xo = epics_signal_r(float, prefix + "X:RBV")
        self.yo = epics_signal_r(float, prefix + "X:RBV")
        self.zo = epics_signal_r(float, prefix + "X:RBV")

        # Spherical coordinates
        self.theta = derived_signal_r(read_theta, x=self.xo, z=self.zo)
        self.rho = derived_signal_r(read_rho, x=self.xo, y=self.yo, z=self.zo)
        self.phi = derived_signal_r(read_phi, x=self.xo, y=self.yo, z=self.zo)

        self.mode = epics_signal_rw(MagnetModes, prefix + "MODE")
        self.ramp_status = epics_signal_rw(MagnetRampStatus, prefix + "RAMPSTATUS")

        self.limit_status = epics_signal_rw(MagnetLimitStatus, prefix + "LIMITSTATUS")
        self.start_ramp = epics_signal_x(prefix + "STARTRAMP.PROC")

        self.tolerance = soft_signal_rw(float, initial_value=0)
        self.timeout = soft_signal_rw(float, initial_value=300)
        self.delay = soft_signal_rw(float, initial_value=5)

        super().__init__(name)

    # Without boundary
    @AsyncStatus.wrap
    async def set(self, value: MagnetPosition):
        await asyncio.gather(
            self.xi.set(value.x),
            self.yi.set(value.y),
            self.zi.set(value.z),
        )
        await self._ramp()

    async def _ramp(self):
        await self.start_ramp.trigger(timeout=1)
        # Due to EPICS flaw, after the callback, still need to wait for a few second for the magnet settle down
        # Is this still needed?
        await asyncio.sleep(await self.delay.get_value())

        ramp_status, limit_status = await asyncio.gather(
            self.ramp_status.get_value(),
            self.limit_status.get_value(),
        )

        if (
            ramp_status == MagnetRampStatus.RAMP_MADE
            and limit_status == MagnetLimitStatus.OK
        ):
            return

        if ramp_status == MagnetRampStatus.RAMPING:
            raise RuntimeError("Magnet still ramping")

        if limit_status == MagnetLimitStatus.VIOLTATION:
            raise RuntimeError("Magnet limit violation")

    async def set_within_boundary(self, value: MagnetPosition):
        """Move magnet while ensuring field magnitude never increases before decreases
        have completed.
        """
        # For keeping the magnitude constrained to avoid quench, always do the decreasing before increasing motors
        x0, y0, z0 = await asyncio.gather(
            self.xo.get_value(),
            self.yo.get_value(),
            self.zo.get_value(),
        )
        x1, y1, z1 = value.x, value.y, value.z

        dx = abs(x1) - abs(x0)
        dy = abs(y1) - abs(y0)
        dz = abs(z1) - abs(z0)

        # Decrease Z first
        if dz < 0:
            await self.zi.set(z1)
            await self._ramp()
        # Then decrease X
        if dx < 0:
            await self.xi.set(x1)
            await self._ramp()
        # Then decrease Y
        if dy < 0:
            await self.yi.set(y1)
            await self._ramp()
        # Finally perform all increases together
        if dx > 0 or dy > 0 or dz > 0:
            await asyncio.gather(
                self.xi.set(x1),
                self.yi.set(y1),
                self.zi.set(z1),
            )
            await self._ramp()
