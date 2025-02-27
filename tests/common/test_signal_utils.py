from unittest.mock import AsyncMock

from dodal.common.signal_utils import create_hardware_backed_soft_signal


async def mock_read_func() -> int:
    return 256


async def test_given_a_hardware_backed_signal_when_read_then_get_from_hardware_called():
    read_func = AsyncMock()
    hardware_signal = create_hardware_backed_soft_signal(int, read_func)
    await hardware_signal.read()
    read_func.assert_called_once()


async def test_given_a_hardware_backed_signal_when_read_then_get_data_from_hardware_func():
    hardware_signal = create_hardware_backed_soft_signal(int, mock_read_func)
    returned_data = await hardware_signal.read()
    assert returned_data[""]["value"] == 256


async def test_given_a_hardware_backed_signal_when_get_value_then_get_data_from_hardware_func():
    hardware_signal = create_hardware_backed_soft_signal(int, mock_read_func)
    returned_data = await hardware_signal.get_value()
    assert returned_data == 256
