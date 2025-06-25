import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.motors import SixAxisGonio


@pytest.fixture
def six_axis_gonio(RE: RunEngine):
    with init_devices(mock=True):
        gonio = SixAxisGonio("")

    return gonio


async def test_reading_six_axis_gonio(six_axis_gonio: SixAxisGonio):
    await assert_reading(
        six_axis_gonio,
        {
            "gonio-omega": partial_reading(0.0),
            "gonio-kappa": partial_reading(0.0),
            "gonio-phi": partial_reading(0.0),
            "gonio-z": partial_reading(0.0),
            "gonio-y": partial_reading(0.0),
            "gonio-x": partial_reading(0.0),
        },
    )
