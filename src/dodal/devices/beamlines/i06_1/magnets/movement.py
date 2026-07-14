import math
from abc import ABC, abstractmethod
from dataclasses import dataclass


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
class MagnetStep:
    x: float | None = None
    y: float | None = None
    z: float | None = None


class MagnetPositionError(Exception):
    pass


class MovementStrategy(ABC):
    @abstractmethod
    def moves(
        self, current: MagnetPosition, target: MagnetPosition
    ) -> list[MagnetStep]:
        """Return a sequence of safe moves."""


class SphericalMovement(MovementStrategy):
    def moves(
        self, current: MagnetPosition, target: MagnetPosition
    ) -> list[MagnetStep]:
        steps: list[MagnetStep] = []

        decreases = [
            ("z", current.z, target.z),
            ("x", current.x, target.x),
            ("y", current.y, target.y),
        ]

        for axis, old, new in decreases:
            if abs(new) < abs(old):
                kwargs = {axis: new}
                steps.append(MagnetStep(**kwargs))

        if any(abs(new) > abs(old) for _, old, new in decreases):
            steps.append(MagnetStep(x=target.x, y=target.y, z=target.z))

        return steps


class CubicMovement(MovementStrategy):
    LIMIT = 1.5

    def moves(
        self, current: MagnetPosition, target: MagnetPosition
    ) -> list[MagnetStep]:
        for axis in (target.x, target.y, target.z):
            if abs(axis) > self.LIMIT:
                raise MagnetPositionError(
                    f"Target {target} outside cubic operating region limit of {self.LIMIT}"
                )

        return [MagnetStep(x=target.x, y=target.y, z=target.z)]


class PlanarXZMovement(MovementStrategy):
    LIMIT = 2.0

    def moves(
        self, current: MagnetPosition, target: MagnetPosition
    ) -> list[MagnetStep]:
        if target.y != 0:
            raise MagnetPositionError(
                f"Y must remain zero in XZ mode. Requested value was {target.y}"
            )

        hypot = math.hypot(target.x, target.z)
        if hypot > self.LIMIT:
            raise MagnetPositionError(
                f"Outside XZ operating region. math.hypot(x={target.x}, y={target.y}) = {hypot}. Limit is {self.LIMIT}"
            )

        return [MagnetStep(x=target.x, z=target.z)]


@dataclass
class UniaxialMovement(MovementStrategy):
    axis: str
    limit: float

    def moves(
        self, current: MagnetPosition, target: MagnetPosition
    ) -> list[MagnetStep]:
        coords = {"x": target.x, "y": target.y, "z": target.z}
        for axis, value in coords.items():
            if axis == self.axis:
                abs_value = abs(value)
                if abs_value > self.limit:
                    raise MagnetPositionError(
                        f"{axis} value of {abs_value} exceeds limit of {self.limit}"
                    )
            elif value != 0:
                raise MagnetPositionError(
                    f"{axis} must remain zero in {self.axis.upper()} mode. Requested value was {value} "
                )

        return [MagnetStep(**{self.axis: coords[self.axis]})]


class QuadrantXYMovement(MovementStrategy):
    """Start from zero field in all axes. Appy 2.o T in + y direction. Move field
    direction through positive quadrant to 2.0 T in the +x direction. At all times
    | B | <= 2.0 T. Ramp field back to zero in x direction.
    """

    LIMIT = 2.0

    def moves(
        self, current: MagnetPosition, target: MagnetPosition
    ) -> list[MagnetStep]:
        if target.z != 0:
            raise MagnetPositionError(
                f"Z must remain zero in QUADRANT_XY mode. You provided {target.z}"
            )

        hypot = math.hypot(target.x, target.y)
        if hypot > self.LIMIT:
            raise MagnetPositionError(
                f"Target math.hypot(x={target.x}, y={target.y}) {hypot} is outside the XY operating region limit of {self.LIMIT}."
            )

        steps: list[MagnetStep] = []

        # Step 1: remove X component first
        if current.x != 0:
            steps.append(MagnetStep(x=0))

        # Step 2: move Y
        if current.y != target.y:
            steps.append(MagnetStep(y=target.y))

        # Step 3: move X to its final value
        if target.x != 0:
            steps.append(MagnetStep(x=target.x))

        return steps
