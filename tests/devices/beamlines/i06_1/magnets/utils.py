from dodal.devices.beamlines.i06_1.magnets.movement import (
    MagnetPosition,
    MagnetSphericalPosition,
)

EXPECTED_CARTESIAN_SPHERICAL_CONVERSION = [
    (MagnetPosition(x=0, y=0, z=1), MagnetSphericalPosition(rho=1, theta=0, phi=90)),
    (MagnetPosition(x=-1, y=0, z=0), MagnetSphericalPosition(rho=1, theta=90, phi=90)),
    (MagnetPosition(x=0, y=1, z=0), MagnetSphericalPosition(rho=1, theta=0, phi=0)),
    (MagnetPosition(x=0, y=-1, z=0), MagnetSphericalPosition(rho=1, theta=0, phi=180)),
]
