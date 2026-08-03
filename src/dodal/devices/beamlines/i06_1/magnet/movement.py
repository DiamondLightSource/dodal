from abc import abstractmethod
from dataclasses import dataclass

from dodal.devices.beamlines.i06_1.magnet.coordinates import (
    MagnetPosition,
    MagnetRequest,
)
from dodal.devices.beamlines.i06_1.magnet.enums import MagnetMode


class MagnetPositionError(Exception):
    @classmethod
    def total_field_mag_outside_limit(
        cls, mode: MagnetMode, limit: float, pos: MagnetPosition
    ):
        return cls(
            f"Target field magnitude of {pos.field_magnitude}T exceeds "
            f"limit of {limit} for mode {mode}. Requested position: {pos}."
        )

    @classmethod
    def axis_below_limit(cls, mode: MagnetMode, limit: float, pos: float, axis: str):
        return cls(
            f"Axis {axis} with value {pos}T is below minimum {limit}T for mode {mode}."
        )

    @classmethod
    def epics_hardware_limit_exceeded(cls, axis: str, pos: float, limit: float):
        return cls(
            f"Requested {axis} axis position {pos}T exceeds EPICS hardware limit "
            f"({limit}T)."
        )


class MovementStrategy:
    """Define the movement and safety constraints for a magnet operating mode.

    A movement strategy validates requested positions against the constraints of a
    particular magnet mode and generates a sequence of safe movement steps to reach
    the requested position. Each generated requested step is validated against the current
    readback before it is applied.
    """

    def _check_epics_hardware_limits(
        self, target_pos: MagnetPosition, limits: MagnetPosition
    ) -> None:
        """Utility method to validate target position against live EPICS PV limits."""
        if abs(target_pos.x) > limits.x:
            raise MagnetPositionError.epics_hardware_limit_exceeded(
                "x", target_pos.x, limits.x
            )
        if abs(target_pos.y) > limits.y:
            raise MagnetPositionError.epics_hardware_limit_exceeded(
                "y", target_pos.y, limits.y
            )
        if abs(target_pos.z) > limits.z:
            raise MagnetPositionError.epics_hardware_limit_exceeded(
                "z", target_pos.z, limits.z
            )

    @abstractmethod
    def check_within_limits(
        self,
        current_readback: MagnetPosition,
        target: MagnetRequest,
        limits: MagnetPosition,
    ) -> None:
        """Validate that a requested position is within the mode's limits.

        Raises:
            MagnetPositionError: If the requested position is invalid or outside
                the limits of this movement strategy.
        """

    @abstractmethod
    def move_steps(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> list[MagnetRequest]:
        """Generate a sequence of safe movement steps to reach the target.

        The returned steps may be used to move through intermediate positions
        required to safely reach the target from the current readback position.
        """


class SphericalMovement(MovementStrategy):
    LIMIT = 1.75
    MODE = MagnetMode.SPHERICAL

    def check_within_limits(
        self,
        current_readback: MagnetPosition,
        target: MagnetRequest,
        limits: MagnetPosition,
    ) -> None:

        mag_pos_after_move = target.resolve_pos(current_readback)
        self._check_epics_hardware_limits(mag_pos_after_move, limits)
        if mag_pos_after_move.field_magnitude > self.LIMIT:
            raise MagnetPositionError.total_field_mag_outside_limit(
                self.MODE, self.LIMIT, mag_pos_after_move
            )

    def move_steps(
        self,
        current_readback: MagnetPosition,
        target: MagnetRequest,
    ) -> list[MagnetRequest]:

        steps: list[MagnetRequest] = []
        decreases = [
            ("z", current_readback.z, target.z),
            ("x", current_readback.x, target.x),
            ("y", current_readback.y, target.y),
        ]
        # Do all decreasing of axes first as one step. This ensures we don't
        # quench the magnet.
        decrease_kwargs = {}
        increase_kwargs = {}
        for axis, old, new in decreases:
            if new is not None and old != new:
                if abs(new) < abs(old):
                    decrease_kwargs[axis] = new
                else:
                    increase_kwargs[axis] = new

        if decrease_kwargs:
            steps.append(MagnetRequest(**decrease_kwargs))
        if increase_kwargs:
            steps.append(MagnetRequest(**increase_kwargs))
        return steps if steps else [target]


class CubicMovement(MovementStrategy):
    MODE = MagnetMode.CUBIC

    def check_within_limits(
        self,
        current_readback: MagnetPosition,
        target: MagnetRequest,
        limits: MagnetPosition,
    ) -> None:
        target_pos = target.resolve_pos(current_readback)
        self._check_epics_hardware_limits(target_pos, limits)

    def move_steps(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> list[MagnetRequest]:
        return [target]


class PlanarXZMovement(MovementStrategy):
    LIMIT = 2.0
    MODE = MagnetMode.PLANAR_XZ

    def check_within_limits(
        self,
        current_readback: MagnetPosition,
        target: MagnetRequest,
        limits: MagnetPosition,
    ) -> None:
        target_pos = target.resolve_pos(current_readback)
        self._check_epics_hardware_limits(target_pos, limits)

        if target_pos.field_magnitude > self.LIMIT:
            raise MagnetPositionError.total_field_mag_outside_limit(
                self.MODE, self.LIMIT, target_pos
            )

    def move_steps(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> list[MagnetRequest]:
        return [MagnetRequest(x=target.x, z=target.z)]


@dataclass
class UniaxialMovement(MovementStrategy):
    mode: MagnetMode

    def _target_axes_map(self, target: MagnetRequest) -> dict[str, float | None]:
        return {
            "x": target.x,
            "y": target.y,
            "z": target.z,
        }

    def check_within_limits(
        self,
        current_readback: MagnetPosition,
        target: MagnetRequest,
        limits: MagnetPosition,
    ) -> None:
        target_pos = target.resolve_pos(current_readback)
        self._check_epics_hardware_limits(target_pos, limits)

    def move_steps(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> list[MagnetRequest]:
        axis = self.mode.axis_alias
        return [MagnetRequest(**{axis: self._target_axes_map(target)[axis]})]


class QuadrantXYMovement(MovementStrategy):
    """Start from zero field in all axes. Appy 2.0 T in + y direction. Move field
    direction through positive quadrant to 2.0 T in the +x direction. At all times
    | B | <= 2.0 T. Ramp field back to zero in x direction.
    """

    LIMIT = 2.0
    MODE = MagnetMode.QUADRANT_XY

    def check_within_limits(
        self,
        current_readback: MagnetPosition,
        target: MagnetRequest,
        limits: MagnetPosition,
    ) -> None:
        target_pos = target.resolve_pos(current_readback)
        self._check_epics_hardware_limits(target_pos, limits)
        # Positive quadrant only as manual state`Move field direction through positive quadrant.`
        if target_pos.x < 0:
            raise MagnetPositionError.axis_below_limit(
                self.MODE, 0.0, target_pos.x, "x"
            )

        if target_pos.y < 0:
            raise MagnetPositionError.axis_below_limit(
                self.MODE, 0.0, target_pos.y, "y"
            )

        if target_pos.field_magnitude > self.LIMIT:
            raise MagnetPositionError.total_field_mag_outside_limit(
                self.MODE, self.LIMIT, target_pos
            )

    def move_steps(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> list[MagnetRequest]:
        steps: list[MagnetRequest] = []

        # If increasing Y while X is non-zero could exceed the field limit,
        # reduce X before increasing Y.
        if (
            target.y is not None
            and target.y > current_readback.y
            and current_readback.x > 0
            and MagnetPosition(x=current_readback.x, y=target.y, z=0).field_magnitude
            >= self.LIMIT
        ):
            steps.append(MagnetRequest(x=0))
            steps.append(MagnetRequest(x=0, y=target.y, z=target.z))

        steps.append(MagnetRequest(x=target.x, y=target.y, z=target.z))
        return steps
