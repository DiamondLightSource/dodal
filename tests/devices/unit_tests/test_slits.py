import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, set_mock_value

from dodal.devices.slits import Slits


@pytest.fixture
async def slits() -> Slits:
    async with init_devices(mock=True):
        slits = Slits("DEMO-SLITS-01:")

    return slits


async def test_reading_slits_reads_gaps_and_centres(slits: Slits):
    set_mock_value(slits.x_gap.user_readback, 0.5)
    set_mock_value(slits.y_centre.user_readback, 1.0)
    set_mock_value(slits.y_gap.user_readback, 1.5)

    await assert_reading(
        slits,
        {
            "slits-x_centre": {
                "value": 0.0,
            },
            "slits-x_gap": {
                "value": 0.5,
            },
            "slits-y_centre": {
                "value": 1.0,
            },
            "slits-y_gap": {
                "value": 1.5,
            },
        },
    )
