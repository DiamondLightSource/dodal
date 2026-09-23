import pytest
from ophyd_async.core import get_mock_put, init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i15_1.attenuators import (
    FastAttenuator,
    FastAttenuatorDemand,
    FastAttenuatorState,
    SlowAttenuator,
    SlowAttenuatorPositions,
)


@pytest.fixture
async def slow_attenuator():
    with init_devices(mock=True):
        slow_attenuator = SlowAttenuator("")
    return slow_attenuator


@pytest.fixture
async def fast_attenuator():
    with init_devices(mock=True):
        fast_attenuator = FastAttenuator("")
    return fast_attenuator


async def test_given_an_attenuator_device_setting_a_valid_position_enum_sets_this_to_the_device(
    slow_attenuator,
):
    await slow_attenuator.set(SlowAttenuatorPositions.TRANS_0_001)
    get_mock_put(slow_attenuator.transmission).assert_called_once_with(
        SlowAttenuatorPositions.TRANS_0_001
    )


async def test_given_attenuator_device_in_position_then_can_read(slow_attenuator):
    set_mock_value(slow_attenuator.transmission, "100%")
    await assert_reading(
        slow_attenuator,
        {
            "slow_attenuator-transmission": partial_reading("100%"),
        },
    )


@pytest.mark.parametrize(
    "transmission, expected_position",
    [
        (100, SlowAttenuatorPositions.TRANS_100),
        (50, SlowAttenuatorPositions.TRANS_50),
        (10, SlowAttenuatorPositions.TRANS_10),
        (1, SlowAttenuatorPositions.TRANS_1),
        (0.1, SlowAttenuatorPositions.TRANS_0_1),
        (0.01, SlowAttenuatorPositions.TRANS_0_01),
        (0.001, SlowAttenuatorPositions.TRANS_0_001),
    ],
)
def test_transmission_float_is_converted_to_position(transmission, expected_position):
    assert SlowAttenuatorPositions.from_trans_float(transmission) is expected_position


def test_unsupported_transmission_float_raises_value_error():
    with pytest.raises(
        ValueError,
        match=(
            "Unsupported transmission: 2. "
            "Supported transmissions are: 100%, 50%, 10%, 1%, 0.1%, 0.01%, 0.001%"
        ),
    ):
        SlowAttenuatorPositions.from_trans_float(2)


async def test_moving_fast_attenuator_in_sets_readback(fast_attenuator):
    await fast_attenuator.set(FastAttenuatorDemand.IN)
    await assert_reading(
        fast_attenuator,
        {
            "fast_attenuator-status": partial_reading(FastAttenuatorState.IN),
        },
    )


async def test_moving_fast_attenuator_out_sets_readback(fast_attenuator):
    await fast_attenuator.set(FastAttenuatorDemand.OUT)
    await assert_reading(
        fast_attenuator,
        {
            "fast_attenuator-status": partial_reading(FastAttenuatorState.OUT),
        },
    )
