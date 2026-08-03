import asyncio
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
    TimeoutCalculator,
    WatchableAsyncStatus,
    callback_on_mock_execute,
    callback_on_mock_put,
    default_mock_class,
    derived_signal_rw,
    error_if_none,
    set_mock_value,
    wait_for_value,
)
from ophyd_async.epics.core import (
    epics_signal_r,
    epics_signal_rw,
    epics_triggerable_command,
)
from pydantic import BaseModel, Field

from dodal.devices.beamlines.i06_1.magnet.coordinates import (
    MagnetPosition,
    MagnetRequest,
    MagnetSphericalPosition,
    MagnetSphericalRequest,
)
from dodal.devices.beamlines.i06_1.magnet.enums import (
    MagnetLimitStatus,
    MagnetMode,
    MagnetRampStatus,
)
from dodal.devices.beamlines.i06_1.magnet.movement import (
    CubicMovement,
    MagnetPositionError,
    MovementStrategy,
    PlanarXZMovement,
    QuadrantXYMovement,
    SphericalMovement,
    UniaxialMovement,
)
from dodal.devices.beamlines.i06_1.magnet.ramp_controller import (
    MagnetAxisRampRateController,
    MagnetThreeAxesRampRateController,
)


class MagnetMoveWithinBoundary(Protocol):
    async def __call__(self, value: MagnetRequest): ...


class FlyMagnetInfo(BaseModel):
    start_position: float = Field(frozen=True)
    end_position: float = Field(frozen=True)
    ramp_rate: float = Field(frozen=True, gt=0)


@dataclass
class MagnetAxisMovableLogic(MovableLogic[float]):
    axis_mode: MagnetMode
    magnet_set_within_boundary: MagnetMoveWithinBoundary

    async def move(self, new_position: float, timeout: TimeoutCalculator) -> None:
        values = {self.axis_mode.axis_alias: new_position}
        await self.magnet_set_within_boundary(MagnetRequest(**values))


@default_mock_class(DeviceMock)
# Don't want to sync readback and setpoint. IOC behaviour will move readback to demand
# once start_ramp is triggered. This logic lives in the SuperConductingMagnetController.
class MagnetAxis(StandardReadable, StandardMovable[float], Flyable, Preparable):
    """Represents one cartesian axis of a superconducting vector magnet.

    Although each axis can be moved independently, all moves are delegated to
    the parent :class:`SuperConductingMagnetController` so that coordinated motion can
    enforce safe field transitions before updating the underlying demand PVs.

    Each axis is associated with a :class:`MagnetAxisRampRateController`, which is used
    to configure the axis ramp rate during preparation for fly scans.
    """

    def __init__(
        self,
        prefix: str,
        axis_mode: MagnetMode,
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
            axis_mode=axis_mode,
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


class MagnetCartesianCoordinates(StandardReadable, Movable[MagnetPosition]):
    """Cartesian interface to the superconducting magnet.

    Exposes the physical X, Y and Z magnet axes as individual movable signals,
    together with a grouped ``MagnetPosition`` interface for moving all three axes
    simultaneously.

    Individual axis moves and grouped cartesian moves are delegated to the parent
    ``SuperConductingMagnetController``, which applies the active movement strategy for the
    current operating mode before commanding the hardware.
    """

    def __init__(
        self,
        prefix: str,
        ramp_rate: MagnetThreeAxesRampRateController,
        mag_within_boundary: MagnetMoveWithinBoundary,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.x = MagnetAxis(
                prefix + "X:", MagnetMode.UNIAXIAL_X, ramp_rate.x, mag_within_boundary
            )
            self.y = MagnetAxis(
                prefix + "Y:", MagnetMode.UNIAXIAL_Y, ramp_rate.y, mag_within_boundary
            )
            self.z = MagnetAxis(
                prefix + "Z:", MagnetMode.UNIAXIAL_Z, ramp_rate.z, mag_within_boundary
            )
        self._set_mag_within_boundary = mag_within_boundary
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: MagnetRequest):
        await self._set_mag_within_boundary(value)

    async def get_readback_position(self) -> MagnetPosition:
        x0, y0, z0 = await asyncio.gather(
            self.x.readback.get_value(),
            self.y.readback.get_value(),
            self.z.readback.get_value(),
        )
        return MagnetPosition(x=x0, y=y0, z=z0)


class MagnetSphericalCoordinates(StandardReadable, Movable[MagnetSphericalPosition]):
    """Spherical coordinate interface to the superconducting magnet.

    Exposes the magnet field in spherical coordinates using the derived signals
    ``rho``, ``theta`` and ``phi``. These signals are calculated from the
    underlying cartesian magnet axes and may also be written individually or as a
    complete ``MagnetSphericalRequest``.

    Writes are converted to cartesian coordinates before being delegated to the
    parent ``SuperConductingMagnetController``, allowing the active movement strategy to
    determine a safe sequence of cartesian moves.
    """

    def __init__(
        self,
        cart: MagnetCartesianCoordinates,
        set_mag_within_boundary: MagnetMoveWithinBoundary,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.theta = derived_signal_rw(
                MagnetPosition.calc_theta, self._set_theta, x=cart.x, z=cart.z
            )
            self.rho = derived_signal_rw(
                MagnetPosition.calc_rho, self._set_rho, x=cart.x, y=cart.y, z=cart.z
            )
            self.phi = derived_signal_rw(
                MagnetPosition.calc_phi, self._set_phi, x=cart.x, y=cart.y, z=cart.z
            )
        self._set_mag_within_boundary = set_mag_within_boundary
        self._cart_ref = Reference(cart)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: MagnetSphericalRequest):
        """Set the requested spherical coordinates.

        Any unspecified spherical coordinates are taken from the current magnet
        readback position. The resulting complete spherical position is converted
        to Cartesian coordinates and passed to the movement controller, which
        determines a safe sequence of Cartesian moves for the active magnet mode.
        """
        current_readback = await self._cart_ref().get_readback_position()
        target = value.resolve_pos(current_readback.to_spherical())
        await self._set_mag_within_boundary(target.to_cartesian().to_request_pos())

    async def _set_rho(self, rho: float):
        await self.set(MagnetSphericalRequest(rho=rho))

    async def _set_theta(self, theta: float):
        await self.set(MagnetSphericalRequest(theta=theta))

    async def _set_phi(self, phi: float):
        await self.set(MagnetSphericalRequest(phi=phi))


class MockSuperConductingMagnetController(
    DeviceMock["SuperConductingMagnetController"]
):
    """Add additional callback logic to our device to get the mock behaviour to simulate
    the hardware as best we can.
    """

    async def connect(self, device: "SuperConductingMagnetController"):

        async def _trigger_start_ramp():
            # Whenever ramp is triggered for the ioc, readback values move to the
            # demand values. Simulate this behaviour here.
            x_d, y_d, z_d = await asyncio.gather(
                device.cart.x.demand.get_value(),
                device.cart.y.demand.get_value(),
                device.cart.z.demand.get_value(),
            )
            set_mock_value(device.ramp_status, MagnetRampStatus.RAMPING)
            set_mock_value(device.cart.x.readback, x_d)
            set_mock_value(device.cart.y.readback, y_d)
            set_mock_value(device.cart.z.readback, z_d)
            set_mock_value(device.ramp_status, MagnetRampStatus.RAMP_MADE)

        callback_on_mock_execute(device.start_ramp, _trigger_start_ramp)

        async def _set_mode(value):
            # Whenever mode is set, ioc automatically sets everything to zero and
            # triggers a ramp.
            set_mock_value(device.cart.x.demand, 0.0)
            set_mock_value(device.cart.y.demand, 0.0)
            set_mock_value(device.cart.z.demand, 0.0)
            await _trigger_start_ramp()

        callback_on_mock_put(device.mode, _set_mode)
        set_mock_value(device.limit_status, MagnetLimitStatus.OK)
        set_mock_value(device.ramp_status, MagnetRampStatus.RAMP_MADE)


@default_mock_class(MockSuperConductingMagnetController)
class SuperConductingMagnetController(StandardReadable):
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

    _MODE_MOVEMENT_STRATEGY: dict[MagnetMode, MovementStrategy] = {
        MagnetMode.SPHERICAL: SphericalMovement(),
        MagnetMode.CUBIC: CubicMovement(),
        MagnetMode.PLANAR_XZ: PlanarXZMovement(),
        MagnetMode.QUADRANT_XY: QuadrantXYMovement(),
        MagnetMode.UNIAXIAL_X: UniaxialMovement(MagnetMode.UNIAXIAL_X, 2.0),
        MagnetMode.UNIAXIAL_Y: UniaxialMovement(MagnetMode.UNIAXIAL_Y, 2.0),
        MagnetMode.UNIAXIAL_Z: UniaxialMovement(MagnetMode.UNIAXIAL_Z, 6.0),
    }

    def __init__(
        self,
        prefix: str,
        ramp_controllers: MagnetThreeAxesRampRateController,
        name: str = "",
    ):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.mode = epics_signal_rw(MagnetMode, prefix + "MODE")

        with self.add_children_as_readables():
            self.cart = MagnetCartesianCoordinates(
                prefix, ramp_controllers, self.set_within_boundary
            )
            self.sph = MagnetSphericalCoordinates(self.cart, self.set_within_boundary)

        self.ramp_status = epics_signal_rw(MagnetRampStatus, prefix + "RAMPSTATUS")
        self.limit_status = epics_signal_rw(MagnetLimitStatus, prefix + "LIMITSTATUS")
        self.start_ramp = epics_triggerable_command(prefix + "STARTRAMP.PROC")

        # Used to block parallel moves that are not submitted together. Allows us to
        # always be sure we safely move the magnet using coordinated logic.
        self._moving = False

        super().__init__(name)

    async def _trigger_ramp(self):
        # Setting invalid demand values should put the limit status in violation state.
        # Block ramp if in violation state.
        limit_status = await self.limit_status.get_value()
        if limit_status == MagnetLimitStatus.VIOLATION:
            raise MagnetPositionError(f"{self.limit_status.name} is at {limit_status}")
        self.log.info("About to start ramping the magnet.")
        await self.start_ramp.trigger()
        await wait_for_value(self.ramp_status, MagnetRampStatus.RAMP_MADE, timeout=None)
        self.log.info(
            f"Ramping complete. Ramp status is now {MagnetRampStatus.RAMP_MADE}"
        )

    async def _apply_step(self, step: MagnetRequest) -> None:
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
        self.log.info(f"About to set demand values of the magnet to {step}.")
        await asyncio.gather(*tasks)
        await self._trigger_ramp()

    async def set_within_boundary(self, value: MagnetRequest):
        """Move the magnet to a new cartesian position.

        Any coordinates left as ``None`` retain their current values. The requested
        target position is validated against the current magnet operating mode and
        converted into a sequence of movement steps by the corresponding movement
        strategy. Each step is then applied sequentially until the requested target
        position is reached.
        """
        if self._moving:
            raise RuntimeError(
                f"Cannot do move for {self.name}. It is already moving. For simultaneous "
                f"moving of axes, please use {self.cart.name} or {self.sph.name}."
            )
        try:
            self._moving = True
            current_readback, mode = await asyncio.gather(
                self.cart.get_readback_position(), self.mode.get_value()
            )
            movement_strategy = self._MODE_MOVEMENT_STRATEGY.get(mode)
            if movement_strategy is None:
                raise ValueError(
                    f"No movement strategy has been configured for device {self.name} for mode {mode}."
                )
            self.log.debug(
                f"Attempting move in mode {mode} with parameters {value}. "
                f"Current readback is {current_readback}."
            )
            # Check final requested position is within limits.
            movement_strategy.check_within_limits(current_readback, value)
            for step in movement_strategy.move_steps(current_readback, value):
                self.log.debug(
                    f"Applying movement step {step}. Current readback is {current_readback}."
                )
                # Check each generated step with the current readback is within limits.
                movement_strategy.check_within_limits(current_readback, step)
                await self._apply_step(step)
                current_readback = await self.cart.get_readback_position()
        finally:
            self._moving = False
