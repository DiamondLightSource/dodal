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
    def axis_outside_limit(cls, mode: MagnetMode, limit: float, pos: float, axis: str):
        return cls(
            f"Axis {axis} with value {pos} exceeds limit {limit}T for mode {mode}."
        )

    @classmethod
    def axis_must_be_zero(cls, mode: MagnetMode, axis: str, value: float):
        return cls(
            f"Axis {axis} must remain zero for mode {mode}. Requested value was {value}T."
        )

    @classmethod
    def axis_below_limit(cls, mode: MagnetMode, limit: float, pos: float, axis: str):
        return cls(
            f"Axis {axis} with value {pos}T is below minimum {limit}T for mode {mode}."
        )


class MovementStrategy:
    def check_within_limits(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> None:
        pass

    @abstractmethod
    def move_steps(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> list[MagnetRequest]:
        """Return a sequence of safe moves."""


class SphericalMovement(MovementStrategy):
    LIMIT = 1.75
    MODE = MagnetMode.SPHERICAL

    def check_within_limits(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> None:
        mag_pos_after_move = target.resolve_pos(current_readback)
        if mag_pos_after_move.field_magnitude > self.LIMIT:
            raise MagnetPositionError.total_field_mag_outside_limit(
                self.MODE, self.LIMIT, mag_pos_after_move
            )

    def move_steps(
        self, current_readback: MagnetPosition, target: MagnetRequest
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
            if new is not None:
                if abs(new) < abs(old):
                    decrease_kwargs[axis] = new
                if abs(new) > abs(old):
                    increase_kwargs[axis] = new

        if decrease_kwargs:
            steps.append(MagnetRequest(**decrease_kwargs))
        if increase_kwargs:
            steps.append(MagnetRequest(**increase_kwargs))
        return steps


class CubicMovement(MovementStrategy):
    LIMIT = 1.5
    MODE = MagnetMode.CUBIC

    def check_within_limits(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> None:
        for axis, value in (
            ("x", target.x),
            ("y", target.y),
            ("z", target.z),
        ):
            if value is not None and abs(value) > self.LIMIT:
                raise MagnetPositionError.axis_outside_limit(
                    self.MODE, self.LIMIT, value, axis
                )

    def move_steps(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> list[MagnetRequest]:
        return [target]


class PlanarXZMovement(MovementStrategy):
    LIMIT = 2.0
    MODE = MagnetMode.PLANAR_XZ

    def check_within_limits(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> None:
        if target.y is not None and target.y != 0:
            raise MagnetPositionError.axis_must_be_zero(self.MODE, "y", target.y)
        new_total_pos = target.resolve_pos(current_readback)
        if new_total_pos.field_magnitude > self.LIMIT:
            raise MagnetPositionError.total_field_mag_outside_limit(
                self.MODE, self.LIMIT, new_total_pos
            )

    def move_steps(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> list[MagnetRequest]:
        return [MagnetRequest(x=target.x, z=target.z)]


@dataclass
class UniaxialMovement(MovementStrategy):
    mode: MagnetMode
    limit: float

    def _target_axes_map(self, target: MagnetRequest) -> dict[str, float | None]:
        return {
            "x": target.x,
            "y": target.y,
            "z": target.z,
        }

    def check_within_limits(
        self, current_readback: MagnetPosition, target: MagnetRequest
    ) -> None:
        for axis, value in self._target_axes_map(target).items():
            if value is None:
                continue

            if axis == self.mode.axis_alias:
                abs_value = abs(value)
                if abs_value > self.limit:
                    raise MagnetPositionError.axis_outside_limit(
                        self.mode, self.limit, abs_value, axis
                    )
            elif value != 0:
                raise MagnetPositionError.axis_must_be_zero(self.mode, axis, value)

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
    ) -> None:
        target_pos = target.resolve_pos(current_readback)

        if target_pos.z != 0:
            raise MagnetPositionError.axis_must_be_zero(self.MODE, "z", target_pos.z)

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
                self.MODE, self.LIMIT, target.resolve_pos(current_readback)
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

        steps.append(MagnetRequest(x=target.x, y=target.y, z=target.z))
        return steps
