from typing import Any
from unittest.mock import AsyncMock

import pytest

from dodal.common.signal_utils import (
    create_hardware_backed_soft_signal,
    create_rw_hardware_backed_soft_signal,
)


async def mock_read_func() -> int:
    return 256


def do_nothing_on_write_rw_hardware_backed_signal(data_type: type, read_func):
    async def do_nothing(value: Any):
        pass

    return create_rw_hardware_backed_soft_signal(data_type, read_func, do_nothing)


@pytest.mark.parametrize(
    "create_hardware_func",
    [create_hardware_backed_soft_signal, do_nothing_on_write_rw_hardware_backed_signal],
)
async def test_given_a_hardware_backed_signal_when_read_then_get_from_hardware_called(
    create_hardware_func,
):
    read_func = AsyncMock()
    hardware_signal = create_hardware_func(int, read_func)
    await hardware_signal.read()
    read_func.assert_called_once()


@pytest.mark.parametrize(
    "create_hardware_func",
    [create_hardware_backed_soft_signal, do_nothing_on_write_rw_hardware_backed_signal],
)
async def test_given_a_hardware_backed_signal_when_read_then_get_data_from_hardware_func(
    create_hardware_func,
):
    hardware_signal = create_hardware_func(int, mock_read_func)
    returned_data = await hardware_signal.read()
    assert returned_data[""]["value"] == 256


@pytest.mark.parametrize(
    "create_hardware_func",
    [create_hardware_backed_soft_signal, do_nothing_on_write_rw_hardware_backed_signal],
)
async def test_given_a_hardware_backed_signal_when_get_value_then_get_data_from_hardware_func(
    create_hardware_func,
):
    hardware_signal = create_hardware_func(int, mock_read_func)
    returned_data = await hardware_signal.get_value()
    assert returned_data == 256


async def test_given_a_rw_hardware_backed_signal_when_set_then_calls_set_method():
    set_func = AsyncMock()
    hardware_signal = create_rw_hardware_backed_soft_signal(
        int, mock_read_func, set_func
    )
    await hardware_signal.set(500)
    set_func.assert_called_once_with(500)


async def test_given_a_rw_hardware_backed_signal_when_set_then_readback_does_not_change():
    set_func = AsyncMock()
    hardware_signal = create_rw_hardware_backed_soft_signal(
        int, mock_read_func, set_func
    )
    await hardware_signal.set(500)
    assert (await hardware_signal.get_value()) == 256
