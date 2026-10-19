import math

from dodal.devices.beamlines.i06_1.magnet.coordinates import (
    MagnetPosition,
    MagnetSphericalPosition,
)

EXPECTED_CARTESIAN_SPHERICAL_CONVERSION = [
    (MagnetPosition(x=0, y=1, z=0), MagnetSphericalPosition(rho=1, theta=0, phi=0)),
    (MagnetPosition(x=0, y=0, z=1), MagnetSphericalPosition(rho=1, theta=0, phi=90)),
    (MagnetPosition(x=0, y=-1, z=0), MagnetSphericalPosition(rho=1, theta=0, phi=180)),
    (MagnetPosition(x=-1, y=0, z=0), MagnetSphericalPosition(rho=1, theta=90, phi=90)),
    (MagnetPosition(x=0, y=0, z=-1), MagnetSphericalPosition(rho=1, theta=180, phi=90)),
    (MagnetPosition(x=1, y=0, z=0), MagnetSphericalPosition(rho=1, theta=270, phi=90)),
    # 45 degree increments
    (
        MagnetPosition(x=-math.sqrt(2) / 2, y=0, z=math.sqrt(2) / 2),
        MagnetSphericalPosition(rho=1, theta=45, phi=90),
    ),
    (
        MagnetPosition(x=-math.sqrt(2) / 2, y=0, z=-math.sqrt(2) / 2),
        MagnetSphericalPosition(rho=1, theta=135, phi=90),
    ),
    (
        MagnetPosition(x=math.sqrt(2) / 2, y=0, z=-math.sqrt(2) / 2),
        MagnetSphericalPosition(rho=1, theta=225, phi=90),
    ),
    (
        MagnetPosition(x=math.sqrt(2) / 2, y=0, z=math.sqrt(2) / 2),
        MagnetSphericalPosition(rho=1, theta=315, phi=90),
    ),
]
