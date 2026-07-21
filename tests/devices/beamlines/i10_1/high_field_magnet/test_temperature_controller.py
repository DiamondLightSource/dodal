import asyncio

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    partial_reading,
)

from dodal.devices.beamlines.i10_1.high_field_magnet.temperature_controller import (
    HFMTemperatureController,
)


@pytest.fixture
def hfm_temp_controller() -> HFMTemperatureController:
    with init_devices(mock=True):
        hfm_temp_controller = HFMTemperatureController(
            prefix="I10J-MAGNET-01:TEMP:",
            suffix="TTEMP:SET",
        )
    return hfm_temp_controller


async def test_temperature_controller_readback(
    hfm_temp_controller: HFMTemperatureController,
):
    await hfm_temp_controller.set(1.0)

    await assert_reading(
        hfm_temp_controller,
        {
            "hfm_temp_controller": partial_reading(1.0),
            "hfm_temp_controller-sensor2": partial_reading(0.0),
            "hfm_temp_controller-sensor3": partial_reading(0.0),
        },
    )
    await assert_configuration(
        hfm_temp_controller,
        {
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
