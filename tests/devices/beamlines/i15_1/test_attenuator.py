import pytest
from ophyd_async.core import get_mock_put, init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i15_1.attenuator import Attenuator, AttenuatorPositions


@pytest.fixture
async def attenuator():
    with init_devices(mock=True):
        attenuator = Attenuator("")
    return attenuator


async def test_given_an_attenuator_device_setting_a_valid_position_enum_sets_this_to_the_device(
    attenuator,
):
    await attenuator.set(AttenuatorPositions.TRANS_0_001)
    get_mock_put(attenuator.transmission).assert_called_once_with(
        AttenuatorPositions.TRANS_0_001
    )


async def test_given_attenuator_device_in_position_then_can_read(attenuator):
    set_mock_value(attenuator.transmission, "100%")
    await assert_reading(
        attenuator,
        {
            "attenuator-transmission": partial_reading("100%"),
        },
    )
