import asyncio

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    partial_reading,
)

from dodal.devices.beamlines.i10_1.high_field_magnet.temperature_controller import (
    HighFieldMagnetTemperatureController,
)


@pytest.fixture
def hfm_temp_controller() -> HighFieldMagnetTemperatureController:
    with init_devices(mock=True):
        hfm_temp_controller = HighFieldMagnetTemperatureController(
            prefix="I10J-MAGNET-01:TEMP:",
            suffix="TTEMP:SET",
            sensor_map={"Sorb": "", "he3_low": "2", "he3_high": "3"},
        )
    return hfm_temp_controller


async def test_temperature_controller_readback(
    hfm_temp_controller: HighFieldMagnetTemperatureController,
):

    # await assert_reading(
    #     hfm_temp_controller.sensor.channel["Sorb"],
    #     {
    #         "hfm_temp_controller-sensor-Sorb": partial_reading(0.0),
    #         "hfm_temp_controller-sensor-he3_low": partial_reading(0.0),
    #         "hfm_temp_controller-sensor-he3_high": partial_reading(0.0),
    #     },
    # )
    await assert_configuration(
        hfm_temp_controller,
        {
            "hfm_temp_controller-tolerance": partial_reading(0.1),
            "hfm_temp_controller-user_setpoint": partial_reading(0.0),
            "hfm_temp_controller-sensor-active_sensor_name": partial_reading("Sorb"),
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


async def test_temperature_controller_sensor_switch(
    hfm_temp_controller: HighFieldMagnetTemperatureController,
):
    assert await hfm_temp_controller.sensor.active_sensor_name.get_value() == "Sorb"
    await hfm_temp_controller.sensor.set("he3_low")
    assert await hfm_temp_controller.sensor.active_sensor_name.get_value() == "he3_low"
    await hfm_temp_controller.sensor.set("he3_high")
    assert await hfm_temp_controller.sensor.active_sensor_name.get_value() == "he3_high"
    await hfm_temp_controller.sensor.set("Sorb")
    assert await hfm_temp_controller.sensor.active_sensor_name.get_value() == "Sorb"
