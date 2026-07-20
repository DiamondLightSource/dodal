import asyncio

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    partial_reading,
)

from dodal.devices.beamlines.i06_1.magnet.temperature_controller import (
    SCMTemperatureController,
)


@pytest.fixture
def scm_temp_controller() -> SCMTemperatureController:
    with init_devices(mock=True):
        scm_temp_controller = SCMTemperatureController(
            prefix="I06J-MAGNET-01::",
            infix="LOOP1",
        )
    return scm_temp_controller


async def test_temperature_controller_readback(
    scm_temp_controller: SCMTemperatureController,
):
    await scm_temp_controller.set(1.0)
    await assert_reading(
        scm_temp_controller,
        {
            "scm_temp_controller": partial_reading(1.0),
            "scm_temp_controller-sensor-sensor2": partial_reading(0.0),
        },
    )

    await assert_configuration(
        scm_temp_controller,
        {
            "scm_temp_controller-tolerance": partial_reading(0.1),
            "scm_temp_controller-user_setpoint": partial_reading(1.0),
            "scm_temp_controller-sensor-sensor_slope": partial_reading(0.0),
            "scm_temp_controller-sensor-sensor_offset": partial_reading(0.0),
            "scm_temp_controller-sensor-sensor_min": partial_reading(0.0),
            "scm_temp_controller-sensor-sensor_max": partial_reading(0.0),
            "scm_temp_controller-sensor-sensor2_slope": partial_reading(0.0),
            "scm_temp_controller-sensor-sensor2_offset": partial_reading(0.0),
            "scm_temp_controller-sensor-sensor2_min": partial_reading(0.0),
            "scm_temp_controller-sensor-sensor2_max": partial_reading(0.0),
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
