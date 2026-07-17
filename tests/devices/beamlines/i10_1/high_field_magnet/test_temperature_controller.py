import asyncio

import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    partial_reading,
)

from dodal.devices.beamlines.i10_1.high_field_magnet.temperature_controller import (
    TemperatureController,
)


@pytest.fixture
def hfm_temp_controller() -> TemperatureController:
    with init_devices(mock=True):
        hfm_temp_controller = TemperatureController.from_prefix(
            prefix="I10J-MAGNET-01:TEMP:",
            suffix="TTEMP:SET",
        )
    return hfm_temp_controller


async def test_temperature_controller_readback(
    hfm_temp_controller: TemperatureController,
):
    await hfm_temp_controller.set(1.0)

    await assert_reading(
        hfm_temp_controller,
        {
            "hfm_temp_controller": partial_reading(1.0),
        },
    )
    await assert_configuration(
        hfm_temp_controller,
        {
            "hfm_temp_controller-sensor-config_2": partial_reading(0.0),
            "hfm_temp_controller-sensor-config_3": partial_reading(0.0),
            "hfm_temp_controller-tolerance": partial_reading(0.1),
            "hfm_temp_controller-user_setpoint": partial_reading(1.0),
        },
    )
    await asyncio.gather(
        hfm_temp_controller.pid.p.set(1.0),
        hfm_temp_controller.pid.i.set(2.0),
        hfm_temp_controller.pid.d.set(3.0),
    )
    await assert_reading(
        hfm_temp_controller.pid,
        {
            "hfm_temp_controller-pid-p": partial_reading(1.0),
            "hfm_temp_controller-pid-i": partial_reading(2.0),
            "hfm_temp_controller-pid-d": partial_reading(3.0),
        },
    )


async def test_temperature_controller_stop(hfm_temp_controller: TemperatureController):

    set_mock_value(hfm_temp_controller.user_setpoint, 1.0)
    set_mock_value(hfm_temp_controller.sensor.temperature, 0.5)
    await hfm_temp_controller.stop()
    await assert_reading(
        hfm_temp_controller,
        {
            "hfm_temp_controller": partial_reading(0.5),
        },
    )
