import pytest
from ophyd_async.core import get_mock_put, init_devices

from dodal.devices.beamlines.i15_1.attenuator import Attenuator, AttenuatorPositions


def test_given_valid_position_can_convert_float_into_enum():
    assert AttenuatorPositions.from_float(0.01) == AttenuatorPositions.TRANS_0_01


def test_given_valid_position_can_convert_int_into_enum():
    assert AttenuatorPositions.from_float(1) == AttenuatorPositions.TRANS_1


def test_given_invalid_position_then_sensible_error_on_converting_into_enum():
    with pytest.raises(ValueError) as e:
        AttenuatorPositions.from_float(2)
    assert "100%, 50%," in e.value.args[0]


@pytest.fixture
async def attenuator():
    with init_devices(mock=True):
        attenuator = Attenuator("")
    return attenuator


async def test_given_an_attenuator_device_setting_a_valid_position_enum_sets_this_to_the_device(
    attenuator,
):
    await attenuator.set(AttenuatorPositions.TRANS_0_001)
    get_mock_put(attenuator._positioner).assert_called_once_with(
        AttenuatorPositions.TRANS_0_001
    )


async def test_given_an_attenuator_device_setting_a_valid_float_sets_this_to_the_device(
    attenuator,
):
    await attenuator.set(10)
    get_mock_put(attenuator._positioner).assert_called_once_with(
        AttenuatorPositions.TRANS_10
    )


async def test_given_an_attenuator_device_setting_an_invalid_float_raises_and_doesnt_set_device(
    attenuator,
):
    with pytest.raises(ValueError) as e:
        await attenuator.set(2)
    assert "100%, 50%," in e.value.args[0]
    get_mock_put(attenuator._positioner).assert_not_called()
