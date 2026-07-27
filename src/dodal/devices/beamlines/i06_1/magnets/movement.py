import math
from abc import abstractmethod
from dataclasses import dataclass

from dodal.devices.beamlines.i06_1.magnets.enums import MagnetMode


def read_theta(x: float, z: float) -> float:
    theta = math.degrees(math.atan2(-x, z))
    return theta % 360


def read_rho(x: float, y: float, z: float) -> float:
    return math.hypot(x, y, z)


def read_phi(x: float, y: float, z: float) -> float:
    return math.degrees(math.atan2(math.hypot(x, z), y))


@dataclass(kw_only=True)
class MagnetPosition:
    x: float
    y: float
    z: float

    def to_spherical(self) -> "MagnetSphericalPosition":
        return MagnetSphericalPosition(
            rho=read_rho(self.x, self.y, self.z),
            theta=read_theta(self.x, self.z),
            phi=read_phi(self.x, self.y, self.z),
        )

    @property
    def field_magnitude(self) -> float:
        return math.hypot(self.x, self.y, self.z)


@dataclass(kw_only=True)
class MagnetSphericalPosition:
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


@dataclass(frozen=True, kw_only=True)
class MagnetPositionRequest:
    x: float | None = None
    y: float | None = None
    z: float | None = None

    def __post_init__(self):
        if self.x is None and self.y is None and self.z is None:
            raise ValueError("At least one of x, y, or z must be specified.")

    def total_position(self, current: MagnetPosition) -> MagnetPosition:
        """Use a current position to fill in empty values. Useful when needing to know
        total position for future moves if they are within limits.
        """
        return MagnetPosition(
            x=current.x if self.x is None else self.x,
            y=current.y if self.y is None else self.y,
            z=current.z if self.z is None else self.z,
        )


class MagnetPositionError(Exception):
    pass

    @classmethod
    def total_field_mag_outside_limit(
        cls, mode: MagnetMode, limit: float, pos: MagnetPosition
    ):
        return cls(
            f"Target field magnitude of {pos.field_magnitude} T exceeds "
            f"limit of {limit} for mode {mode}. "
            f"math.hypot(x={pos.x}, z={pos.z}, y={pos.y}) = {pos.field_magnitude}."
        )

    @classmethod
    def axis_outside_limit(cls, mode: MagnetMode, limit: float, pos: float, axis: str):
        return cls(
            f"Axis {axis} with value {pos} exceeds limit {limit} T for mode {mode}. "
        )


class MovementStrategy:
    def check_within_limits(
        self, current: MagnetPosition, target: MagnetPositionRequest
    ) -> None:
        pass

    @abstractmethod
    def move_steps(
        self, current: MagnetPosition, target: MagnetPositionRequest
    ) -> list[MagnetPositionRequest]:
        """Return a sequence of safe moves."""


class SphericalMovement(MovementStrategy):
    LIMIT = 1.75
    MODE = MagnetMode.SPHERICAL

    def check_within_limit(
        self, current: MagnetPosition, target: MagnetPositionRequest
    ) -> None:
        mag_pos_after_move = target.total_position(current)
        if mag_pos_after_move.field_magnitude > self.LIMIT:
            raise MagnetPositionError.total_field_mag_outside_limit(
                self.MODE, self.LIMIT, mag_pos_after_move
            )

    def move_steps(
        self, current: MagnetPosition, target: MagnetPositionRequest
    ) -> list[MagnetPositionRequest]:

        steps: list[MagnetPositionRequest] = []

        decreases = [
            ("z", current.z, target.z),
            ("x", current.x, target.x),
            ("y", current.y, target.y),
        ]

        # Do all decreasing of axes first as one step. This ensures we don't
        # quench the magnet.
        decrease_kwargs = {}
        for axis, old, new in decreases:
            if new is not None and abs(new) < abs(old):
                decrease_kwargs[axis] = new

        if decrease_kwargs:
            steps.append(MagnetPositionRequest(**decrease_kwargs))

        increase_kwargs = {}
        for axis, old, new in decreases:
            if new is not None and abs(new) > abs(old):
                increase_kwargs[axis] = new

        if increase_kwargs:
            steps.append(MagnetPositionRequest(**increase_kwargs))

        return steps


class CubicMovement(MovementStrategy):
    LIMIT = 1.5
    MODE = MagnetMode.CUBIC

    def check_within_limits(
        self, current: MagnetPosition, target: MagnetPositionRequest
    ) -> None:
        for _, value in (
            ("x", target.x),
            ("y", target.y),
            ("z", target.z),
        ):
            if value is not None and abs(value) > self.LIMIT:
                raise MagnetPositionError(
                    f"Target {target} outside region limit of {self.LIMIT} for mode {self.MODE}"
                )

    def move_steps(
        self, current: MagnetPosition, target: MagnetPositionRequest
    ) -> list[MagnetPositionRequest]:
        return [target]


class PlanarXZMovement(MovementStrategy):
    LIMIT = 2.0
    MODE = MagnetMode.PLANAR_XZ

    def check_within_limits(
        self, current: MagnetPosition, target: MagnetPositionRequest
    ) -> None:
        if target.y is not None and target.y != 0:
            raise MagnetPositionError(
                f"Y must remain zero in XZ mode. Requested value was {target.y}"
            )
        new_total_pos = target.total_position(current)
        if new_total_pos.field_magnitude > self.LIMIT:
            raise MagnetPositionError.total_field_mag_outside_limit(
                self.MODE, self.LIMIT, new_total_pos
            )

    def move_steps(
        self, current: MagnetPosition, target: MagnetPositionRequest
    ) -> list[MagnetPositionRequest]:
        return [MagnetPositionRequest(x=target.x, z=target.z)]


@dataclass
class UniaxialMovement(MovementStrategy):
    mode: MagnetMode
    limit: float

    def _target_axes_map(
        self, target: MagnetPositionRequest
    ) -> dict[str, float | None]:
        return {
            "x": target.x,
            "y": target.y,
            "z": target.z,
        }

    def check_within_limits(
        self, current: MagnetPosition, target: MagnetPositionRequest
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
                raise MagnetPositionError(
                    f"{axis} must remain zero in {self.mode} mode. "
                    f"Requested value was {value}"
                )

    def move_steps(
        self, current: MagnetPosition, target: MagnetPositionRequest
    ) -> list[MagnetPositionRequest]:
        axis = self.mode.axis_alias
        return [MagnetPositionRequest(**{axis: self._target_axes_map(target)[axis]})]


class QuadrantXYMovement(MovementStrategy):
    """Start from zero field in all axes. Appy 2.0 T in + y direction. Move field
    direction through positive quadrant to 2.0 T in the +x direction. At all times
    | B | <= 2.0 T. Ramp field back to zero in x direction.
    """

    LIMIT = 2.0
    MODE = MagnetMode.QUADRANT_XY

    def check_within_limits(
        self, current: MagnetPosition, target: MagnetPositionRequest
    ) -> None:
        if target.z is not None and target.z != 0:
            raise MagnetPositionError(
                f"Z must remain zero in QUADRANT_XY mode. You provided {target.z}"
            )
        new_total_pos = target.total_position(current)
        if new_total_pos.field_magnitude > self.LIMIT:
            raise MagnetPositionError.total_field_mag_outside_limit(
                self.MODE, self.LIMIT, new_total_pos
            )

    def move_steps(
        self, current: MagnetPosition, target: MagnetPositionRequest
    ) -> list[MagnetPositionRequest]:
        steps: list[MagnetPositionRequest] = []

        # Step 1: remove X component first
        if target.x is not None and current.x != 0:
            steps.append(MagnetPositionRequest(x=0))

        # Step 2: move Y
        if target.y is not None and current.y != target.y:
            steps.append(MagnetPositionRequest(y=target.y))

        # Step 3: move X to its final value
        if target.x is not None and target.x != 0:
            steps.append(MagnetPositionRequest(x=target.x))

        return steps
