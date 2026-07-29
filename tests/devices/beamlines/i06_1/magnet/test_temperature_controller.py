import asyncio

import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    partial_reading,
)

from dodal.devices.beamlines.i06_1.magnet.temperature_controller import (
    SuperConductingMagnetTemperatureController,
)


@pytest.fixture
def scm_temp_controller() -> SuperConductingMagnetTemperatureController:
    with init_devices(mock=True):
        scm_temp_controller = SuperConductingMagnetTemperatureController(
            prefix="I06J-MAGNET-01::",
            infix="LOOP1",
        )
    return scm_temp_controller


async def test_temperature_controller_readback(
    scm_temp_controller: SuperConductingMagnetTemperatureController,
):

    await assert_reading(
        scm_temp_controller,
        {
            "scm_temp_controller-sensor-channel1": partial_reading(0.0),
            "scm_temp_controller-sensor-channel2": partial_reading(0.0),
        },
    )

    await assert_configuration(
        scm_temp_controller,
        {
            "scm_temp_controller-tolerance": partial_reading(0.1),
            "scm_temp_controller-user_setpoint": partial_reading(0.0),
            "scm_temp_controller-sensor-channel1-slope": partial_reading(0.0),
            "scm_temp_controller-sensor-channel1-offset": partial_reading(0.0),
            "scm_temp_controller-sensor-channel1-min": partial_reading(0.0),
            "scm_temp_controller-sensor-channel1-max": partial_reading(0.0),
            "scm_temp_controller-sensor-channel2-slope": partial_reading(0.0),
            "scm_temp_controller-sensor-channel2-offset": partial_reading(0.0),
            "scm_temp_controller-sensor-channel2-min": partial_reading(0.0),
            "scm_temp_controller-sensor-channel2-max": partial_reading(0.0),
            "scm_temp_controller-ramp_rate": partial_reading(0.0),
            "scm_temp_controller-ramp_mode": partial_reading(""),
        },
    )
    await asyncio.gather(
        scm_temp_controller.pid.p.set(1.0),
        scm_temp_controller.pid.i.set(2.0),
        scm_temp_controller.pid.d.set(3.0),
    )
    await assert_reading(
        scm_temp_controller.pid,
        {
            "scm_temp_controller-pid-p": partial_reading(1.0),
            "scm_temp_controller-pid-i": partial_reading(2.0),
            "scm_temp_controller-pid-d": partial_reading(3.0),
        },
    )

    # await assert_reading(
    #     scm_temp_controller.sensor.sensor2,
    #     {
    #         "scm_temp_controller-sensor-channel2": partial_reading(0.0),
    #     },
    # )


async def test_temperature_controller_sensor_switch(
    scm_temp_controller: SuperConductingMagnetTemperatureController,
):
    await scm_temp_controller.sensor.set("sensor2")
    assert await scm_temp_controller.sensor.active_sensor_name.get_value() == "sensor2"
    await scm_temp_controller.sensor.set("sensor")
    assert await scm_temp_controller.sensor.active_sensor_name.get_value() == "sensor"


async def test_scmc(scm_temp_controller: SuperConductingMagnetTemperatureController):

    sensor = scm_temp_controller.sensor
    await sensor.active_sensor_name.set("sensor2")

    assert await sensor.active_sensor.get_value() == 0
    set_mock_value(sensor.channel[2].sensor, 1)
    assert await sensor.active_sensor.get_value() == 1

    await sensor.active_sensor_name.set("sensor1")
    assert await sensor.active_sensor.get_value() == 0
    set_mock_value(sensor.channel[1].sensor, 2)
    assert await sensor.active_sensor.get_value() == 2

    await sensor.active_sensor_name.set("sensor2")
    assert await sensor.active_sensor.get_value() == 1
