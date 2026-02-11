import asyncio

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.b07 import B07SampleManipulator52B


@pytest.fixture
def sm52b() -> B07SampleManipulator52B:
    with init_devices(mock=True):
        sm52b = B07SampleManipulator52B(prefix="TEST:")
    return sm52b


@pytest.mark.parametrize(
    "x, y, z, xp, yp, zp, roty, rotz, kappa, phi, omega",
    [
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (1.23, 2.40, 0.0, 0.0, 0.0, 0.0, 1.0, 1.2, 0, 2.0, 1.7),
        (1.23, 2.40, 3.51, 24.0, 1.0, 2.0, 5.0, 21.0, 1.0, 25.0, 19.2),
    ],
)
async def test_sm_read(
    sm52b: B07SampleManipulator52B,
    x: float,
    y: float,
    z: float,
    xp: float,
    yp: float,
    zp: float,
    roty: float,
    rotz: float,
    kappa: float,
    phi: float,
    omega: float,
) -> None:
    await asyncio.gather(
        sm52b.x.set(x),
        sm52b.y.set(y),
        sm52b.z.set(z),
        sm52b.xp.set(xp),
        sm52b.yp.set(yp),
        sm52b.zp.set(zp),
        sm52b.roty.set(roty),
        sm52b.rotz.set(rotz),
        sm52b.kappa.set(kappa),
        sm52b.phi.set(phi),
        sm52b.omega.set(omega),
    )
    await assert_reading(
        sm52b,
        {
            "sm52b-x": partial_reading(x),
            "sm52b-y": partial_reading(y),
            "sm52b-z": partial_reading(z),
            "sm52b-xp": partial_reading(xp),
            "sm52b-yp": partial_reading(yp),
            "sm52b-zp": partial_reading(zp),
            "sm52b-roty": partial_reading(roty),
            "sm52b-rotz": partial_reading(rotz),
            "sm52b-kappa": partial_reading(int(kappa)),
            "sm52b-phi": partial_reading(int(phi)),
            "sm52b-omega": partial_reading(int(omega)),
        },
    )
