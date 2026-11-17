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
    signal = mock_simple_panda._trigger
    set_mock_value(signal, True)

    description = await mock_simple_panda.describe()
    expected_timestamp_description = dict(description["mock_simple_panda-_trigger"])
    expected_timestamp_description["dtype"] = "number"
    assert (
        description["mock_simple_panda-_trigger-timestamp"]
        == expected_timestamp_description
    )

    reading = await mock_simple_panda.read()
    assert (
        reading["mock_simple_panda-_trigger-timestamp"]["value"]
        == reading["mock_simple_panda-_trigger"]["timestamp"]
    )
    assert (
        reading["mock_simple_panda-_trigger-timestamp"]["timestamp"]
        == reading["mock_simple_panda-_trigger"]["timestamp"]
    )
