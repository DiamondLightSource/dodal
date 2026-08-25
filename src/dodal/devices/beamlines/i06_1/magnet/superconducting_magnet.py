import asyncio
from dataclasses import dataclass
from functools import cached_property
from typing import Protocol

from bluesky.protocols import Flyable, Movable, Preparable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
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
from dodal.devices.beamlines.i06_1.magnet.power_supply import (
    MagnetAxisPowerSupply,
    ThreeMagnetAxisPowerSupply,
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
        psu: MagnetAxisPowerSupply,
        magnet_set_within_boundary: MagnetMoveWithinBoundary,
        name: str = "",
    ):
        self.psu_ref = Reference(psu)

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
        await self.psu_ref().ramp_rate.set(value.ramp_rate)
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
        psu: ThreeMagnetAxisPowerSupply,
        mag_within_boundary: MagnetMoveWithinBoundary,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.x = MagnetAxis(
                prefix + "X:", MagnetMode.UNIAXIAL_X, psu.x, mag_within_boundary
            )
            self.y = MagnetAxis(
                prefix + "Y:", MagnetMode.UNIAXIAL_Y, psu.y, mag_within_boundary
            )
            self.z = MagnetAxis(
                prefix + "Z:", MagnetMode.UNIAXIAL_Z, psu.z, mag_within_boundary
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
    """Mock controller that simulates the behaviour of the
    SuperConductingMagnetController hardware.

    The mock reproduces additional IOC behaviour that is not provided by the
    standard device mock, including:

    - Updating readback positions when a ramp is triggered.
    - Resetting demand positions and configuring PSU limits when the mode
      changes.
    - Updating ramp and limit status signals.
    - Simulating the movement of readback positions over time.

    Movements are simulated over multiple steps by default so that beamline
    operation in mock mode behaves similarly to the real hardware. This also
    allows fly scans to be exercised in mock mode, with detector events
    occurring while the magnet is moving.

    Unit tests that do not require simulated movement can disable it by
    setting ``steps`` to zero::

        scmc = SuperConductingMagnetController(...)
        await scmc.connect(mock=MockSuperConductingMagnetController(steps=0))

    Args:
        name: Name of the mock device.
        parent: Parent mock device, if any.
        steps: Number of intermediate positions used to simulate a movement.
            A value less than or equal to zero makes movements instantaneous.
        ramp_time: Total time in seconds over which a simulated movement takes
            place. The time is divided equally between ``steps``.
    """

    # Pulled directly from live IOC so can replicate behaviour in mock mode.
    PSU_AXIS_LIMITS: dict[MagnetMode, tuple[float, float, float]] = {
        MagnetMode.UNIAXIAL_X: (2, 0, 0),
        MagnetMode.UNIAXIAL_Y: (0, 2, 0),
        MagnetMode.UNIAXIAL_Z: (0, 0, 6),
        MagnetMode.CUBIC: (2, 2, 2),
        MagnetMode.QUADRANT_XY: (2, 2, 2),
        MagnetMode.PLANAR_XZ: (2, 0, 2),
        MagnetMode.SPHERICAL: (2, 2, 2),
    }

    def __init__(
        self,
        name: str = "",
        parent: DeviceMock | None = None,
        steps: int = 10,
        ramp_time: float = 1.0,
    ):
        super().__init__(name, parent)
        self._steps = steps
        self._ramp_time = ramp_time

    async def connect(self, device: "SuperConductingMagnetController"):
        async def _trigger_start_ramp():
            # Whenever ramp is triggered for the ioc, readback values move to the
            # demand values. Simulate this behaviour here.
            x_d, y_d, z_d = await asyncio.gather(
                device.cart.x.demand.get_value(),
                device.cart.y.demand.get_value(),
                device.cart.z.demand.get_value(),
            )

            x_r, y_r, z_r = await asyncio.gather(
                device.cart.x.readback.get_value(),
                device.cart.y.readback.get_value(),
                device.cart.z.readback.get_value(),
            )

            set_mock_value(device.ramp_status, MagnetRampStatus.RAMPING)

            if self._steps <= 0:
                set_mock_value(device.cart.x.readback, x_d)
                set_mock_value(device.cart.y.readback, y_d)
                set_mock_value(device.cart.z.readback, z_d)
            else:
                for step in range(1, self._steps + 1):
                    fraction = step / self._steps

                    set_mock_value(device.cart.x.readback, x_r + (x_d - x_r) * fraction)
                    set_mock_value(device.cart.y.readback, y_r + (y_d - y_r) * fraction)
                    set_mock_value(device.cart.z.readback, z_r + (z_d - z_r) * fraction)

                    if self._ramp_time:
                        await asyncio.sleep(self._ramp_time / self._steps)

            set_mock_value(device.ramp_status, MagnetRampStatus.RAMP_MADE)

        callback_on_mock_execute(device._start_ramp, _trigger_start_ramp)  # noqa: SLF001

        async def _set_mode(mode: MagnetMode):
            # Whenever mode is set, ioc automatically sets everything to zero and
            # triggers a ramp.
            set_mock_value(device.cart.x.demand, 0.0)
            set_mock_value(device.cart.y.demand, 0.0)
            set_mock_value(device.cart.z.demand, 0.0)
            _configure_axis_limit(mode)

            await _trigger_start_ramp()

        def _configure_axis_limit(mode: MagnetMode) -> None:
            x, y, z = self.PSU_AXIS_LIMITS[mode]
            set_mock_value(device.psu_ref().x.limit, x)
            set_mock_value(device.psu_ref().y.limit, y)
            set_mock_value(device.psu_ref().z.limit, z)

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
        psu: ThreeMagnetAxisPowerSupply,
        name: str = "",
    ):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.mode = epics_signal_rw(MagnetMode, prefix + "MODE")

        with self.add_children_as_readables():
            self.cart = MagnetCartesianCoordinates(
                prefix, psu, self.set_within_boundary
            )
            self.sph = MagnetSphericalCoordinates(self.cart, self.set_within_boundary)

        self.ramp_status = epics_signal_rw(MagnetRampStatus, prefix + "RAMPSTATUS")
        self.limit_status = epics_signal_rw(MagnetLimitStatus, prefix + "LIMITSTATUS")
        # Make private so cannot trigger without going through magnet API.
        self._start_ramp = epics_triggerable_command(prefix + "STARTRAMP.PROC")

        self.psu_ref = Reference(psu)
        # Used to block parallel moves that are not submitted together. Allows us to
        # always be sure we safely move the magnet using coordinated logic.
        self._moving = False

        super().__init__(name)

    async def _trigger_ramp(self, timeout: float = DEFAULT_TIMEOUT):
        # Setting invalid demand values should put the limit status in violation state.
        # Block ramp if in violation state.
        limit_status = await self.limit_status.get_value()
        if limit_status == MagnetLimitStatus.VIOLATION:
            raise MagnetPositionError(f"{self.limit_status.name} is at {limit_status}")
        self.log.info("About to start ramping the magnet.")
        await self._start_ramp.trigger()
        await wait_for_value(
            self.ramp_status, MagnetRampStatus.RAMP_MADE, timeout=timeout
        )
        self.log.info(
            f"Ramping complete. Ramp status is now {MagnetRampStatus.RAMP_MADE}"
        )

    async def _apply_step(
        self, step: MagnetRequest, timeout: float = DEFAULT_TIMEOUT
    ) -> None:
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
        await self._trigger_ramp(timeout=timeout)

    async def set_within_boundary(self, value: MagnetRequest):
        """Move the magnet to a new cartesian position while respecting mode limits.

        Any coordinates left as ``None`` retain their current values. The requested
        target position is first validated against the limits of the current magnet
        operating mode. The corresponding movement strategy then generates a sequence
        of intermediate movement steps.

        Each movement step is validated against the latest magnet readback before it
        is applied. The readback position is updated after each step, ensuring that
        subsequent steps are validated against the magnet's actual current position.
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
            await self.psu_ref().check_axes_within_limit(value, mode)
            for step in movement_strategy.move_steps(current_readback, value):
                self.log.debug(
                    f"Applying movement step {step}. Current readback is {current_readback}."
                )
                # Check each generated step is also within limit.
                await self.psu_ref().check_axes_within_limit(step, mode)
                movement_strategy.check_within_limits(current_readback, step)
                timeout = await self.calculate_timeout_per_step(
                    current_readback=current_readback, value=step
                )
                await self._apply_step(step, timeout=timeout)
                current_readback = await self.cart.get_readback_position()
        finally:
            self._moving = False

    async def calculate_timeout_per_step(
        self, current_readback: MagnetPosition, value: MagnetRequest
    ) -> float:
        """Calculate the timeout for a move based on the distance to move and the ramp rate."""
        ramp_rates = await self.psu_ref().get_ramp_rate()
        targets = (value.x, value.y, value.z)
        currents = (current_readback.x, current_readback.y, current_readback.z)

        max_axis_time = max(
            abs(target - current) / rate if target is not None and rate > 0 else 0.0
            for target, current, rate in zip(targets, currents, ramp_rates, strict=True)
        )

        return max_axis_time + DEFAULT_TIMEOUT
