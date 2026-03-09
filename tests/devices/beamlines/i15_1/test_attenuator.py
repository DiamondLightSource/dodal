import pytest
from ophyd_async.core import get_mock_put, init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i15_1.attenuator import Attenuator, AttenuatorPositions


@pytest.mark.parametrize(
    "number, enum",
    [
        [100, AttenuatorPositions.TRANS_100],
        [10, AttenuatorPositions.TRANS_10],
        [1, AttenuatorPositions.TRANS_1],
        [0.1, AttenuatorPositions.TRANS_0_1],
        [0.01, AttenuatorPositions.TRANS_0_01],
        [0.001, AttenuatorPositions.TRANS_0_001],
    ],
)
def test_given_valid_position_can_convert_into_enum(
    number: int | float, enum: AttenuatorPositions
):
    assert AttenuatorPositions.from_float(number) == enum


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
    get_mock_put(attenuator.transmission).assert_called_once_with(
        AttenuatorPositions.TRANS_0_001
    )


@pytest.mark.parametrize(
    "number, enum",
    [
        [100, AttenuatorPositions.TRANS_100],
        [10, AttenuatorPositions.TRANS_10],
        [1, AttenuatorPositions.TRANS_1],
        [0.1, AttenuatorPositions.TRANS_0_1],
        [0.01, AttenuatorPositions.TRANS_0_01],
        [0.001, AttenuatorPositions.TRANS_0_001],
    ],
)
async def test_given_an_attenuator_device_setting_a_valid_float_sets_this_to_the_device(
    attenuator, number, enum
):
    await attenuator.set(number)
    get_mock_put(attenuator.transmission).assert_called_once_with(enum)


async def test_given_an_attenuator_device_setting_an_invalid_float_raises_and_doesnt_set_device(
    attenuator,
):
    with pytest.raises(ValueError) as e:
        await attenuator.set(2)
    assert "100%, 50%," in e.value.args[0]
    get_mock_put(attenuator.transmission).assert_not_called()


async def test_given_attenuator_device_in_position_then_can_read(attenuator):
    set_mock_value(attenuator.transmission, "100%")
    await assert_reading(
        attenuator,
        {
            "attenuator-transmission": partial_reading("100%"),
        },
    )
