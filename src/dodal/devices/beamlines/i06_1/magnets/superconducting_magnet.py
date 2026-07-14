import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property
from typing import Protocol

from bluesky.protocols import Flyable, Movable, Preparable
from ophyd_async.core import (
    AsyncStatus,
    DeviceMock,
    MovableLogic,
    Reference,
    StandardMovable,
    StandardReadable,
    StandardReadableFormat,
    WatchableAsyncStatus,
    callback_on_mock_put,
    default_mock_class,
    derived_signal_rw,
    error_if_none,
    set_mock_value,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_x
from pydantic import BaseModel, Field

from dodal.devices.beamlines.i06_1.magnets.enums import (
    MagnetLimitStatus,
    MagnetModes,
    MagnetRampStatus,
)
from dodal.devices.beamlines.i06_1.magnets.movement import (
    CubicMovement,
    MagnetPosition,
    MagnetPositionError,
    MagnetSphericalPosition,
    MagnetStep,
    MovementStrategy,
    PlanarXZMovement,
    QuadrantXYMovement,
    SphericalMovement,
    UniaxialMovement,
    read_phi,
    read_rho,
    read_theta,
)
from dodal.devices.beamlines.i06_1.magnets.ramp_controller import (
    MagnetAxisRampRateController,
    MagnetThreeAxesRampRateController,
)


class MagnetMoveWithinBoundary(Protocol):
    async def __call__(self, x: float | None, y: float | None, z: float | None): ...


class FlyMagnetInfo(BaseModel):
    start_position: float = Field(frozen=True)
    end_position: float = Field(frozen=True)
    ramp_rate: float = Field(frozen=True, gt=0)


@dataclass
class MagnetAxisMovableLogic(MovableLogic[float]):
    axis: str
    magnet_set_within_boundary: MagnetMoveWithinBoundary

    async def move(
        self, new_position: float, timeout: Callable[[], float | None]
    ) -> None:
        values = {self.axis: new_position}
        # ToDo - feed timeout to here?
        await self.magnet_set_within_boundary(**values)


class MagnetAxis(StandardReadable, StandardMovable[float], Flyable, Preparable):
    """Represents one cartesian axis of a superconducting vector magnet.

    Although each axis can be moved independently, all moves are delegated to
    the parent :class:`SuperConductingMagnet` so that coordinated motion can
    enforce safe field transitions before updating the underlying demand PVs.

    Each axis is associated with a :class:`MagnetAxisRampRateController`, which is used
    to configure the axis ramp rate during preparation for fly scans.
    """

    def __init__(
        self,
        prefix: str,
        axis: str,
        ramp_rate: MagnetAxisRampRateController,
        magnet_set_within_boundary: MagnetMoveWithinBoundary,
        name: str = "",
    ):
        self.ramp_rate_ref = Reference(ramp_rate)

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.readback = epics_signal_r(float, prefix + "RBV")
        self.demand = epics_signal_rw(float, prefix + "DMD")

        self._movable_logic = MagnetAxisMovableLogic(
            readback=self.readback,
            setpoint=self.demand,
            axis=axis,
            magnet_set_within_boundary=magnet_set_within_boundary,
        )

        self._fly_info: FlyMagnetInfo | None = None
        self._fly_status: WatchableAsyncStatus | None = None
        super().__init__(name)

    @cached_property
    def movable_logic(self) -> MagnetAxisMovableLogic:
        return self._movable_logic

    @AsyncStatus.wrap
    async def prepare(self, value: FlyMagnetInfo):
        self._fly_info = value
        await self.ramp_rate_ref().set(value.ramp_rate)
        await self.set(value.start_position)

    @AsyncStatus.wrap
    async def kickoff(self):
        fly_info = error_if_none(
            self._fly_info,
            f"{self.name} must be prepared before attempting to kickoff.",
        )
        self._fly_status = self.set(fly_info.end_position)
        self._fly_info = None

    def complete(self) -> WatchableAsyncStatus:
        fly_status = error_if_none(self._fly_status, f"{self.name} kickoff not called.")
        self._fly_status = None
        return fly_status


class MagnetCartesianCoorindates(StandardReadable, Movable[MagnetPosition]):
    """Cartesian interface to the superconducting magnet.

    Exposes the physical X, Y and Z magnet axes as individual movable signals,
    together with a grouped ``MagnetPosition`` interface for moving all three axes
    simultaneously.

    Individual axis moves and grouped cartesian moves are delegated to the parent
    ``SuperConductingMagnet``, which applies the active movement strategy for the
    current operating mode before commanding the hardware.
    """

    def __init__(
        self,
        prefix: str,
        ramp_rate: MagnetThreeAxesRampRateController,
        set_mag_within_boundary: MagnetMoveWithinBoundary,
        name: str = "",
    ) -> None:
        self._set_mag_within_boundary = set_mag_within_boundary
        with self.add_children_as_readables():
            self.x = MagnetAxis(
                prefix + "X:", "x", ramp_rate.x, set_mag_within_boundary
            )
            self.y = MagnetAxis(
                prefix + "Y:", "y", ramp_rate.y, set_mag_within_boundary
            )
            self.z = MagnetAxis(
                prefix + "Z:", "z", ramp_rate.z, set_mag_within_boundary
            )
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: MagnetPosition):
        await self._set_mag_within_boundary(x=value.x, y=value.y, z=value.z)


class MagnetSphericalCoordinates(StandardReadable, Movable[MagnetSphericalPosition]):
    """Spherical coordinate interface to the superconducting magnet.

    Exposes the magnet field in spherical coordinates using the derived signals
    ``rho``, ``theta`` and ``phi``. These signals are calculated from the
    underlying cartesian magnet axes and may also be written individually or as a
    complete ``MagnetSphericalPosition``.

    Writes are converted to cartesian coordinates before being delegated to the
    parent ``SuperConductingMagnet``, allowing the active movement strategy to
    determine a safe sequence of cartesian moves.
    """

    def __init__(
        self,
        cart: MagnetCartesianCoorindates,
        set_mag_within_boundary: MagnetMoveWithinBoundary,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.theta = derived_signal_rw(
                read_theta, self._set_theta, x=cart.x, z=cart.z
            )
            self.rho = derived_signal_rw(
                read_rho, self._set_rho, x=cart.x, y=cart.y, z=cart.z
            )
            self.phi = derived_signal_rw(
                read_phi,
                self._set_phi,
                x=cart.x,
                y=cart.y,
                z=cart.z,
            )
        self._set_mag_within_boundary = set_mag_within_boundary
        self._cart_ref = Reference(cart)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: MagnetSphericalPosition):
        cart = value.to_cartesian()
        await self._set_mag_within_boundary(x=cart.x, y=cart.y, z=cart.z)

    async def _set_spherical(
        self,
        rho: float | None = None,
        theta: float | None = None,
        phi: float | None = None,
    ):
        x, y, z = await asyncio.gather(
            self._cart_ref().x.readback.get_value(),
            self._cart_ref().y.readback.get_value(),
            self._cart_ref().z.readback.get_value(),
        )
        current = MagnetPosition(x=x, y=y, z=z).to_spherical()
        spherical_pos = MagnetSphericalPosition(
            rho=current.rho if rho is None else rho,
            theta=current.theta if theta is None else theta,
            phi=current.phi if phi is None else phi,
        )
        await self.set(spherical_pos)

    async def _set_rho(self, rho: float):
        await self._set_spherical(rho=rho)

    async def _set_theta(self, theta: float):
        await self._set_spherical(theta=theta)

    async def _set_phi(self, phi: float):
        await self._set_spherical(phi=phi)


MODE_MOVEMENT_STRATEGY: dict[MagnetModes, MovementStrategy] = {
    MagnetModes.SPHERICAL: SphericalMovement(),
    MagnetModes.CUBIC: CubicMovement(),
    MagnetModes.PLANAR_XZ: PlanarXZMovement(),
    MagnetModes.QUADRANT_XY: QuadrantXYMovement(),
    MagnetModes.UNIAXIAL_X: UniaxialMovement("x", limit=2.0),
    MagnetModes.UNIAXIAL_Y: UniaxialMovement("y", limit=2.0),
    MagnetModes.UNIAXIAL_Z: UniaxialMovement("z", limit=6.0),
}


class MockSuperConductingMagnet(DeviceMock["SuperConductingMagnet"]):
    async def connect(self, device: "SuperConductingMagnet"):

        def _set_ramp_status(value):
            set_mock_value(device.ramp_status, MagnetRampStatus.RAMPING)
            set_mock_value(device.ramp_status, MagnetRampStatus.RAMP_MADE)

        def _set_mode(value):
            # Whenever mode is changed, ioc automatically sets everything to zero and ramps
            set_mock_value(device.cart.x.demand, 0.0)
            set_mock_value(device.cart.y.demand, 0.0)
            set_mock_value(device.cart.z.demand, 0.0)
            set_mock_value(device.ramp_status, MagnetRampStatus.RAMPING)
            set_mock_value(device.ramp_status, MagnetRampStatus.RAMP_MADE)

        callback_on_mock_put(device.mode, _set_mode)
        callback_on_mock_put(device.start_ramp, _set_ramp_status)
        set_mock_value(device.limit_status, MagnetLimitStatus.OK)
        set_mock_value(device.ramp_status, MagnetRampStatus.RAMP_MADE)


@default_mock_class(MockSuperConductingMagnet)
class SuperConductingMagnet(StandardReadable):
    """A three-axis superconducting vector magnet.

    The magnet provides both cartesian and spherical coordinate interfaces for
    reading and setting the magnetic field. Cartesian coordinates expose the
    physical X, Y and Z magnet axes, while spherical coordinates provide the
    equivalent field magnitude and orientation.

    The permitted operating region and the sequence of axis movements are
    determined by the current magnet operating mode. Each operating mode uses a
    dedicated movement strategy to validate requested positions and generate a
    safe sequence of cartesian magnet moves before ramping the field.
    """

    def __init__(
        self,
        prefix: str,
        ramp_controllers: MagnetThreeAxesRampRateController,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.cart = MagnetCartesianCoorindates(
                prefix, ramp_controllers, self.set_within_boundary
            )
            self.sph = MagnetSphericalCoordinates(self.cart, self.set_within_boundary)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.mode = epics_signal_rw(MagnetModes, prefix + "MODE")

        self.ramp_status = epics_signal_rw(MagnetRampStatus, prefix + "RAMPSTATUS")

        self.limit_status = epics_signal_rw(MagnetLimitStatus, prefix + "LIMITSTATUS")
        self.start_ramp = epics_signal_x(prefix + "STARTRAMP.PROC")
        self.timeout = 600

        super().__init__(name)

    async def _ramp(self):
        # Setting invalid demand values should put the limit status in violation state.
        # Block ramp if in violation state.
        if await self.limit_status.get_value() == MagnetLimitStatus.VIOLTATION:
            raise MagnetPositionError(
                f"{self.limit_status.name} is at {MagnetLimitStatus.VIOLTATION}"
            )
        self.log.info("About to start ramping the magnet.")
        # ToDo - Use TimeoutCalculated from ophyd-async in new release.
        await self.start_ramp.trigger(timeout=self.timeout)
        await wait_for_value(self.ramp_status, MagnetRampStatus.RAMP_MADE, self.timeout)
        self.log.info("Ramping complete.")

    async def _apply_step(self, step: MagnetStep) -> None:
        """Apply a single movement step and wait for the magnet ramp to complete.

        A movement step may update one or more cartesian axes simultaneously. Once
        the requested demand values have been written, the magnet is instructed to
        ramp and this method waits for the ramp to complete before returning.
        """
        tasks = []
        if step.x is not None:
            tasks.append(self.cart.x.demand.set(step.x))
        if step.y is not None:
            tasks.append(self.cart.y.demand.set(step.y))
        if step.z is not None:
            tasks.append(self.cart.z.demand.set(step.z))

        await asyncio.gather(*tasks)
        await self._ramp()

    async def set_within_boundary(
        self,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None,
    ):
        """Move the magnet to a new cartesian position.

        Any coordinates left as ``None`` retain their current values. The requested
        target position is validated against the current magnet operating mode and
        converted into a sequence of movement steps by the corresponding movement
        strategy. Each step is then applied sequentially until the requested target
        position is reached.
        """
        if x is None and y is None and z is None:
            raise MagnetPositionError("x, y, and z cannot all be None.")
        current = MagnetPosition(
            x=await self.cart.x.readback.get_value(),
            y=await self.cart.y.readback.get_value(),
            z=await self.cart.z.readback.get_value(),
        )
        target = MagnetPosition(
            x=current.x if x is None else x,
            y=current.y if y is None else y,
            z=current.z if z is None else z,
        )
        mode = await self.mode.get_value()
        movement_strategy = MODE_MOVEMENT_STRATEGY[mode]

        self.log.debug(
            f"Attempting move in mode {mode} with parameters {target}. Current position is {current}"
        )

        for step in movement_strategy.moves(current, target):
            await self._apply_step(step)
