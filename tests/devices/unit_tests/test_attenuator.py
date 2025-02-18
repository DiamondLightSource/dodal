import asyncio

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import callback_on_mock_put, set_mock_value

from dodal.devices.attenuator.attenuator import BinaryFilterAttenuator

CALCULATED_VALUE = [True, False, True] * 6  # Some "random" values


@pytest.fixture
async def fake_attenuator():
    async with init_devices(mock=True):
        fake_attenuator: BinaryFilterAttenuator = BinaryFilterAttenuator(
            "", "attenuator"
        )

    return fake_attenuator


async def test_set_transmission_success(fake_attenuator: BinaryFilterAttenuator):
    await fake_attenuator.set(1.0)


def test_set_transmission_in_run_engine(
    fake_attenuator: BinaryFilterAttenuator, RE: RunEngine
):
    RE(bps.abs_set(fake_attenuator, 1, wait=True))


async def test_given_attenuator_sets_filters_to_expected_value_then_set_returns(
    fake_attenuator: BinaryFilterAttenuator,
):
    def mock_apply_values(*args, **kwargs):
        for i in range(16):
            set_mock_value(
                fake_attenuator._calculated_filter_states[i], CALCULATED_VALUE[i]
            )
            set_mock_value(fake_attenuator._filters_in_position[i], CALCULATED_VALUE[i])

    callback_on_mock_put(fake_attenuator._change, mock_apply_values)

    await asyncio.wait_for(fake_attenuator.set(0.65), timeout=0.1)


async def test_given_attenuator_fails_to_set_filters_then_set_timeout(
    fake_attenuator: BinaryFilterAttenuator,
):
    def mock_apply_values(*args, **kwargs):
        for i in range(16):
            set_mock_value(
                fake_attenuator._calculated_filter_states[i], CALCULATED_VALUE[i]
            )

    callback_on_mock_put(fake_attenuator._change, mock_apply_values)

    with pytest.raises(asyncio.exceptions.TimeoutError):
        await asyncio.wait_for(fake_attenuator.set(0.65), timeout=0.01)
