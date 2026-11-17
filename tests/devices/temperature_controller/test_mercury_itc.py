import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.temperature_controller.mercury_itc import MercuryITC


@pytest.fixture
async def mock_mercury():
    with init_devices(mock=True):
        fake_aperture = MercuryITC("test_prefix", "mock_mercury")
    return fake_aperture


async def test_mercury_can_be_read(mock_mercury: MercuryITC):
    set_mock_value(mock_mercury.sensors[0].readback, 75.6)

    await assert_reading(
        mock_mercury,
        {"mock_mercury-sensors-1-readback": partial_reading(75.6)},
    )


async def test_mercury_channels_describe_and_read_timestamps(
    mock_mercury: MercuryITC,
):
    for channel_number in range(1, 4):
        channel = mock_mercury.sensors[channel_number]
        readback_name = channel.readback.name
        timestamp_name = f"{readback_name}-timestamp"

        description = await channel.describe()
        expected_timestamp_description = dict(description[readback_name])
        expected_timestamp_description["dtype"] = "number"
        assert description[timestamp_name] == expected_timestamp_description

        reading = await channel.read()
        assert reading[timestamp_name]["value"] == reading[readback_name]["timestamp"]
        assert (
            reading[timestamp_name]["timestamp"] == reading[readback_name]["timestamp"]
        )
