import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import callback_on_mock_put, set_mock_value

from dodal.devices.attenuator.attenuator import (
    BinaryFilterAttenuator,
    EnumFilterAttenuator,
    YesNo,
)
from dodal.devices.attenuator.filter_selections import (
    I24_FilterOneSelections,
    I24_FilterTwoSelections,
)

CALCULATED_VALUE = [True, False, True] * 6  # Some "random" values


@pytest.fixture
async def fake_attenuator():
    async with init_devices(mock=True):
        fake_attenuator: BinaryFilterAttenuator = BinaryFilterAttenuator(
            prefix="", num_filters=16
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

    await fake_attenuator.set(0.65)


async def test_attenuator_set_only_complete_once_all_filters_in_position(
    fake_attenuator: BinaryFilterAttenuator,
):
    fake_set_complete = asyncio.Event()

    async def mock_apply_values(*args, **kwargs):
        for i in range(16):
            set_mock_value(
                fake_attenuator._calculated_filter_states[i], CALCULATED_VALUE[i]
            )
        await fake_set_complete.wait()
        for i in range(16):
            set_mock_value(fake_attenuator._filters_in_position[i], CALCULATED_VALUE[i])

    callback_on_mock_put(fake_attenuator._change, mock_apply_values)
    status = fake_attenuator.set(0.65)
    assert not status.done
    fake_set_complete.set()
    await status


MOCK_TIMEOUT_S = 0.01


@patch(
    "dodal.devices.attenuator.attenuator.ENUM_ATTENUATOR_SETTLE_TIME_S", MOCK_TIMEOUT_S
)
async def test_enum_attenuator_set():
    with init_devices(mock=True):
        attenuator = EnumFilterAttenuator(
            prefix="",
            filter_selection=(I24_FilterOneSelections, I24_FilterTwoSelections),
        )

    async def _move_filter_after_short_delay(_):
        await asyncio.sleep(MOCK_TIMEOUT_S / 2)
        await attenuator._filters[0].done_move.set(0)

    attenuator._auto_move_on_desired_transmission_set.set = AsyncMock()
    attenuator._use_current_energy.trigger = AsyncMock()
    attenuator._desired_transmission.set = AsyncMock(
        side_effect=_move_filter_after_short_delay
    )
    status = attenuator.set(0.2)
    await asyncio.sleep(MOCK_TIMEOUT_S)
    assert not status.done
    await attenuator._filters[0].done_move.set(1)
    await attenuator._filters[1].done_move.set(1)
    await status
    attenuator._auto_move_on_desired_transmission_set.set.assert_awaited_once_with(
        YesNo.YES
    )
    attenuator._use_current_energy.trigger.assert_called_once()
