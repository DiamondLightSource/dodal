import math
from dataclasses import dataclass


@dataclass(kw_only=True)
class MagnetPosition:
    x: float
    y: float
    z: float

    @staticmethod
    def calc_theta(x: float, z: float) -> float:
        theta = math.degrees(math.atan2(-x, z))
        return theta % 360

    @staticmethod
    def calc_rho(x: float, y: float, z: float) -> float:
        return math.hypot(x, y, z)

    @staticmethod
    def calc_phi(x: float, y: float, z: float) -> float:
        return math.degrees(math.atan2(math.hypot(x, z), y))

    def to_spherical(self) -> "MagnetSphericalPosition":
        return MagnetSphericalPosition(
            rho=self.calc_rho(self.x, self.y, self.z),
            theta=self.calc_theta(self.x, self.z),
            phi=self.calc_phi(self.x, self.y, self.z),
        )

    @property
    def field_magnitude(self) -> float:
        return math.hypot(self.x, self.y, self.z)

    def to_request_pos(self) -> "MagnetRequest":
        return MagnetRequest(x=self.x, y=self.y, z=self.z)


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

    def to_request_pos(self) -> "MagnetSphericalRequest":
        return MagnetSphericalRequest(rho=self.rho, theta=self.theta, phi=self.phi)


@dataclass(frozen=True, kw_only=True)
class MagnetRequest:
    x: float | None = None
    y: float | None = None
    z: float | None = None

    def __post_init__(self):
        if self.x is None and self.y is None and self.z is None:
            raise ValueError("At least one of x, y, or z must be specified.")

    def resolve_pos(self, current: MagnetPosition) -> MagnetPosition:
        """Resolve unspecified coordinates using the current position."""
        return MagnetPosition(
            x=current.x if self.x is None else self.x,
            y=current.y if self.y is None else self.y,
            z=current.z if self.z is None else self.z,
        )


@dataclass(frozen=True, kw_only=True)
class MagnetSphericalRequest:
    rho: float | None = None
    theta: float | None = None
    phi: float | None = None

    def __post_init__(self):
        if self.rho is None and self.theta is None and self.phi is None:
            raise ValueError("At least one of rho, theta, or phi must be specified.")

    def resolve_pos(self, current: MagnetSphericalPosition) -> MagnetSphericalPosition:
        """Resolve unspecified coordinates using the current position."""
        return MagnetSphericalPosition(
            rho=current.rho if self.rho is None else self.rho,
            theta=current.theta if self.theta is None else self.theta,
            phi=current.phi if self.phi is None else self.phi,
        )
