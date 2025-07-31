from ophyd_async.core import StrictEnum, init_devices

from dodal.devices.temperture_controller.lakeshore.lakeshore_io import (
    LakeshoreBaseIO,
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

    control_attribute = [
        "user_setpoint",
        "ramp_rate",
        "ramp_enable",
        "heater_output",
        "heater_output_range",
    ]
    pid_attribute = [
        "p",
        "i",
        "d",
        "manual_output",
    ]

    for attr in control_attribute:
        assert attr in lakeshore.control_channels[1].__dict__["_child_devices"]
    for attr in pid_attribute:
        assert attr in lakeshore.pid_channels[2].__dict__["_child_devices"]
    assert len(lakeshore.control_channels) == no_channels
    assert len(lakeshore.readBack_channel) == no_channels
    assert len(lakeshore.pid_channels) == no_channels
