import asyncio
from typing import Protocol

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    DeviceMock,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    callback_on_mock_execute,
    callback_on_mock_put,
    default_mock_class,
    derived_signal_rw,
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


class MagnetMoveWithinBoundary(Protocol):
    async def __call__(self, value: MagnetRequest): ...


class FlyMagnetInfo(BaseModel):
    start_position: float = Field(frozen=True)
    end_position: float = Field(frozen=True)
    ramp_rate: float = Field(frozen=True, gt=0)


@default_mock_class(DeviceMock)
# Don't want to sync readback and setpoint. IOC behaviour will move readback to demand
# once start_ramp is triggered. This logic lives in the SuperConductingMagnetController.
class MagnetAxis(StandardReadable):
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
        name: str = "",
    ):

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.readback = epics_signal_r(float, prefix + "RBV")
        self.demand = epics_signal_rw(float, prefix + "DMD")
        self.limit = epics_signal_r(float, prefix + ":LIM:FIELD:NOW")
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.ramp_speed = epics_signal_rw(
                float,
                read_pv=prefix + "STS:RAMPRATE:TPM",
                write_pv=prefix + "SET:DMD:RAMPRATE:TPM",
            )
            self.ramp_limit = epics_signal_r(float, prefix + "LIM:RAMPRATE:TPM")
        super().__init__(name)


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
                device.x.demand.get_value(),
                device.y.demand.get_value(),
                device.z.demand.get_value(),
            )
            set_mock_value(device.ramp_status, MagnetRampStatus.RAMPING)
            set_mock_value(device.x.readback, x_d)
            set_mock_value(device.y.readback, y_d)
            set_mock_value(device.z.readback, z_d)
            set_mock_value(device.ramp_status, MagnetRampStatus.RAMP_MADE)

        callback_on_mock_execute(device._start_ramp, _trigger_start_ramp)  # noqa: SLF001

        async def _set_mode(value):
            # Whenever mode is set, ioc automatically sets everything to zero and
            # triggers a ramp.
            set_mock_value(device.x.demand, 0.0)
            set_mock_value(device.y.demand, 0.0)
            set_mock_value(device.z.demand, 0.0)
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
        MagnetMode.UNIAXIAL_X: UniaxialMovement(MagnetMode.UNIAXIAL_X),
        MagnetMode.UNIAXIAL_Y: UniaxialMovement(MagnetMode.UNIAXIAL_Y),
        MagnetMode.UNIAXIAL_Z: UniaxialMovement(MagnetMode.UNIAXIAL_Z),
    }

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.mode = epics_signal_rw(MagnetMode, prefix + "MODE")
        self.x = MagnetAxis(prefix + "X:")
        self.y = MagnetAxis(prefix + "Y:")
        self.z = MagnetAxis(prefix + "Z:")

        self.ramp_status = epics_signal_rw(MagnetRampStatus, prefix + "RAMPSTATUS")
        self.limit_status = epics_signal_rw(MagnetLimitStatus, prefix + "LIMITSTATUS")
        # Make private so cannot trigger without going through magnet API.
        self._start_ramp = epics_triggerable_command(prefix + "STARTRAMP.PROC")
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
        await self._start_ramp.trigger()
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
            tasks.append(self.x.demand.set(step.x))
        if step.y is not None:
            tasks.append(self.y.demand.set(step.y))
        if step.z is not None:
            tasks.append(self.z.demand.set(step.z))
        self.log.info(f"About to set demand values of the magnet to {step}.")
        await asyncio.gather(*tasks)
        await self._trigger_ramp()

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
            raise RuntimeError(f"Cannot do move for {self.name}. It is already moving.")
        try:
            self._moving = True
            current_readback, mode, field_limit = await asyncio.gather(
                self.get_readback_position(),
                self.mode.get_value(),
                self.get_field_limit(),
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
            movement_strategy.check_within_limits(current_readback, value, field_limit)
            for step in movement_strategy.move_steps(current_readback, value):
                self.log.debug(
                    f"Applying movement step {step}. Current readback is {current_readback}."
                )
                # Check each generated step with the current readback is within limits.
                movement_strategy.check_within_limits(
                    current_readback, step, field_limit
                )
                await self._apply_step(step)
                current_readback = await self.get_readback_position()
        finally:
            self._moving = False

    async def get_readback_position(self) -> MagnetPosition:
        """Get the current magnet readback position as a :class:`MagnetPosition`."""
        x, y, z = await asyncio.gather(
            self.x.readback.get_value(),
            self.y.readback.get_value(),
            self.z.readback.get_value(),
        )
        return MagnetPosition(x=x, y=y, z=z)

    async def get_field_limit(self) -> MagnetPosition:
        """Get the current field limit of the magnet.

        The field limit is a live readback from the IOC and may change depending on
        the current magnet operating mode and the current demand values.
        """
        x, y, z = await asyncio.gather(
            self.x.limit.get_value(),
            self.y.limit.get_value(),
            self.z.limit.get_value(),
        )
        return MagnetPosition(x=x, y=y, z=z)


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
        controller: SuperConductingMagnetController,
        name: str = "",
    ) -> None:
        self._controller_ref = Reference(controller)
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.x = derived_signal_rw(
                raw_to_derived=self._read_position,
                set_derived=self._set_x,
                val=self._controller_ref().x.readback,
            )
            self.y = derived_signal_rw(
                raw_to_derived=self._read_position,
                set_derived=self._set_y,
                val=self._controller_ref().y.readback,
            )
            self.z = derived_signal_rw(
                raw_to_derived=self._read_position,
                set_derived=self._set_z,
                val=self._controller_ref().z.readback,
            )

        super().__init__(name)

    def _read_position(self, val: float) -> float:
        """Read the current magnet position as a :class:`MagnetPosition`."""
        return val

    @AsyncStatus.wrap
    async def set(self, value: MagnetRequest):
        await self._controller_ref().set_within_boundary(value)

    async def _set_x(self, x: float):
        await self.set(MagnetRequest(x=x))

    async def _set_y(self, y: float):
        await self.set(MagnetRequest(y=y))

    async def _set_z(self, z: float):
        await self.set(MagnetRequest(z=z))


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
        controller: SuperConductingMagnetController,
        name: str = "",
    ):
        self._controller_ref = Reference(controller)

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.rho = derived_signal_rw(
                raw_to_derived=self._get_spherical_component,
                set_derived=self._set_rho,
                component="rho",
                x=self._controller_ref().x.readback,
                y=self._controller_ref().y.readback,
                z=self._controller_ref().z.readback,
            )
            self.theta = derived_signal_rw(
                raw_to_derived=self._get_spherical_component,
                set_derived=self._set_theta,
                component="theta",
                x=self._controller_ref().x.readback,
                y=self._controller_ref().y.readback,
                z=self._controller_ref().z.readback,
            )
            self.phi = derived_signal_rw(
                raw_to_derived=self._get_spherical_component,
                set_derived=self._set_phi,
                component="phi",
                x=self._controller_ref().x.readback,
                y=self._controller_ref().y.readback,
                z=self._controller_ref().z.readback,
            )
        super().__init__(name)

    def _get_spherical_component(
        self, component: str, x: float, y: float, z: float
    ) -> float:
        cart_pos = MagnetPosition(
            x=x,
            y=y,
            z=z,
        )
        return getattr(cart_pos.to_spherical(), component)

    @AsyncStatus.wrap
    async def set(self, value: MagnetSphericalRequest):
        """Set the requested spherical coordinates.

        Any unspecified spherical coordinates are taken from the current magnet
        readback position. The resulting complete spherical position is converted
        to Cartesian coordinates and passed to the movement controller, which
        determines a safe sequence of Cartesian moves for the active magnet mode.
        """
        current_readback = await self._controller_ref().get_readback_position()
        target = value.resolve_pos(current_readback.to_spherical())
        await self._controller_ref().set_within_boundary(
            target.to_cartesian().to_request_pos()
        )

    async def _set_rho(self, rho: float):
        await self.set(MagnetSphericalRequest(rho=rho))

    async def _set_theta(self, theta: float):
        await self.set(MagnetSphericalRequest(theta=theta))

    async def _set_phi(self, phi: float):
        await self.set(MagnetSphericalRequest(phi=phi))


class SuperConductingMagnet(StandardReadable):
    """Factory function to create a superconducting magnet device with both cartesian and
    spherical coordinate interfaces.
    """

    def __init__(self, controller: SuperConductingMagnetController, name: str = ""):

        with self.add_children_as_readables():
            self.cart = MagnetCartesianCoordinates(controller)
            self.sph = MagnetSphericalCoordinates(controller)
            self.controller = controller

        super().__init__(name)
