import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.slits import Slits, SlitsWithZ


@pytest.fixture
async def slits() -> Slits:
    async with init_devices(mock=True):
        slits = Slits("DEMO-SLITS-01:")

    return slits


@pytest.fixture
async def exit_slits() -> SlitsWithZ:
    async with init_devices(mock=True):
        exit_slits = SlitsWithZ("DEMO-SLITS-02:")

    return exit_slits


async def test_reading_slits_reads_gaps_and_centres(slits: Slits):
    set_mock_value(slits.x_gap.user_readback, 0.5)
    set_mock_value(slits.y_centre.user_readback, 1.0)
    set_mock_value(slits.y_gap.user_readback, 1.5)

    await assert_reading(
        slits,
        {
            "slits-x_centre": partial_reading(0.0),
            "slits-x_gap": partial_reading(0.5),
            "slits-y_centre": partial_reading(1.0),
            "slits-y_gap": partial_reading(1.5),
        },
    )


async def test_reading_exit_slits_reads_gaps_and_centres_and_z(exit_slits: SlitsWithZ):
    set_mock_value(exit_slits.x_gap.user_readback, 0.5)
    set_mock_value(exit_slits.y_centre.user_readback, 1.0)
    set_mock_value(exit_slits.y_gap.user_readback, 1.5)
    set_mock_value(exit_slits.z.user_readback, 22)

    await assert_reading(
        exit_slits,
        {
            "exit_slits-x_centre": partial_reading(0.0),
            "exit_slits-x_gap": partial_reading(0.5),
            "exit_slits-y_centre": partial_reading(1.0),
            "exit_slits-y_gap": partial_reading(1.5),
            "exit_slits-z": partial_reading(22),
        },
    )
