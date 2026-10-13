import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.beamlines.b01_1.diodes import RGBDiodes


@pytest.fixture
async def diodes() -> RGBDiodes:
    async with init_devices(mock=True):
        diodes = RGBDiodes("PANDA:FmcIn:Val", "LOCUM:", green_channel=4)
    return diodes


def test_diodes_use_pvs_for_their_channel(diodes: RGBDiodes) -> None:
    assert diodes.red.source == "mock+ca://PANDA:FmcIn:Val5"
    assert diodes.green.source == "mock+ca://PANDA:FmcIn:Val4"
    assert diodes.blue.source == "mock+ca://PANDA:FmcIn:Val7"
    assert diodes.gain.source == "mock+ca://LOCUM:SETRANGE"
    assert diodes.gain_readback.source == "mock+ca://LOCUM:MRREADBACK"


async def test_diodes_read_values_and_configure_gain(diodes: RGBDiodes) -> None:
    set_mock_value(diodes.red, 1.0)
    set_mock_value(diodes.green, 2.0)
    set_mock_value(diodes.blue, 3.0)
    set_mock_value(diodes.gain, "Auto")
    set_mock_value(diodes.gain_readback, "1uA")

    await assert_reading(
        diodes,
        {
            "diodes-red": partial_reading(1.0),
            "diodes-green": partial_reading(2.0),
            "diodes-blue": partial_reading(3.0),
        },
    )
    await assert_configuration(
        diodes,
        {
            "diodes-gain": partial_reading("Auto"),
            "diodes-gain_readback": partial_reading("1uA"),
        },
    )
