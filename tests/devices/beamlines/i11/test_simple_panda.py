import pytest
from ophyd_async.core import init_devices, set_mock_value

from dodal.devices.beamlines.i11.simple_panda import SimplePanda


@pytest.fixture
async def mock_simple_panda() -> SimplePanda:
    async with init_devices(mock=True):
        simple_panda = SimplePanda("test_prefix", name="mock_simple_panda")
    return simple_panda


async def test_simple_panda_describe_and_read_timestamps(
    mock_simple_panda: SimplePanda,
) -> None:
    signal = mock_simple_panda.signal_to_timestamp
    set_mock_value(signal, True)
    signal_name = signal.name
    timestamp_name = f"{signal_name}-timestamp"

    description = await mock_simple_panda.describe()
    expected_timestamp_description = dict(description[signal_name])
    expected_timestamp_description["dtype"] = "number"
    assert description[timestamp_name] == expected_timestamp_description

    reading = await mock_simple_panda.read()
    assert reading[timestamp_name]["value"] == reading[signal_name]["timestamp"]
    assert reading[timestamp_name]["timestamp"] == reading[signal_name]["timestamp"]
