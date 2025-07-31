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
    no_channels = 4
    prefix = "888"
    async with init_devices(mock=True):
        lakeshore = LakeshoreBaseIO(
            prefix=prefix, no_channels=no_channels, heater_setting=HEATER_SETTING
        )

    control_attribute = [
        "user_setpoint",
        "ramp_rate",
        "ramp_enable",
        "heater_output",
        "heater_output_range",
        "p",
        "i",
        "d",
        "manual_output",
    ]

    for i in range(1, no_channels + 1):
        assert (
            lakeshore.control_channels[i].user_setpoint.source.split("ca://")[-1]
            == f"{prefix}SETP{i}"
        )
        assert (
            lakeshore.readBack_channel[i].source.split("ca://")[-1]
            == f"{prefix}KRDG{i - 1}"
        )

        for attr in control_attribute:
            assert attr in lakeshore.control_channels[i].__dict__["_child_devices"]

    assert len(lakeshore.control_channels) == no_channels
    assert len(lakeshore.readBack_channel) == no_channels


async def test_lakeshoreIO_single_control_creation_success():
    no_channels = 2
    prefix = "888"
    async with init_devices(mock=True):
        lakeshore = LakeshoreBaseIO(
            prefix=prefix,
            no_channels=no_channels,
            heater_setting=HEATER_SETTING,
            single_control_channel=True,
        )

    control_attribute = [
        "user_setpoint",
        "ramp_rate",
        "ramp_enable",
        "heater_output",
        "heater_output_range",
        "p",
        "i",
        "d",
        "manual_output",
    ]

    for attr in control_attribute:
        assert attr in lakeshore.control_channels[1].__dict__["_child_devices"]

    assert (
        lakeshore.control_channels[1].user_setpoint.source.split("ca://")[-1]
        == f"{prefix}SETP"
    )
    for i in range(1, no_channels + 1):
        assert (
            lakeshore.readBack_channel[i].source.split("ca://")[-1]
            == f"{prefix}KRDG{i - 1}"
        )
    assert len(lakeshore.control_channels) == 1
    assert len(lakeshore.readBack_channel) == no_channels
