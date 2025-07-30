from ophyd_async.core import StrictEnum, init_devices

from dodal.devices.temperture_controller.lakeshore.lakeshore_io import (
    LakeshoreBaseIO,
    PIDBaseIO,
)


class HEATER_SETTING(StrictEnum):
    OFF = "Off"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


async def test_lakeshoreIO_creation_success():
    no_channels = 2
    async with init_devices(mock=True):
        lakeshore = LakeshoreBaseIO(
            prefix="888", no_channels=no_channels, heater_setting=HEATER_SETTING
        )

    io_attribute = [
        "user_setpoint",
        "ramp_rate",
        "ramp_enable",
        "heater_output",
        "heater_output_range",
        "user_readback",
    ]
    for i in io_attribute:
        assert i in lakeshore.__dict__["_child_devices"]
        assert len(getattr(lakeshore, i)) == no_channels


async def test_PIDBaseIOcreation_success():
    no_channels = 2
    async with init_devices(mock=True):
        pid = PIDBaseIO(
            prefix="888",
            no_channels=no_channels,
        )

    io_attribute = [
        "p",
        "i",
        "d",
        "manual_output",
    ]
    for i in io_attribute:
        assert i in pid.__dict__["_child_devices"]
        assert len(getattr(pid, i)) == no_channels
