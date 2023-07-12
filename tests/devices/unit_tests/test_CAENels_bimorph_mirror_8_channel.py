import pytest
from bluesky import RunEngine

from dodal.devices.bimorph_mirrors.CAENels_bimorph_mirror_8_channel import (
    CAENelsBimorphMirror8Channel,
    OnOff,
    OperationMode,
)

from enum import Enum
class ChannelTypes(Enum):
    VTRGT = "VTRGT",
    VTRGT_RBV = "VTRGT_RBV",
    SHIFT = "SHIFT",
    VOUT = "VOUT",
    VOUT_RBV = "VOUT_RBV",
    STATUS = "STATUS"

def get_channels(bimorph8, channel_type):
    """
    Just takes an 8-chanel bimorph and returns a list of relevant the channel components
    """
    if channel_type == ChannelTypes.VTRGT:
        return [
            bimorph8.channel_1_voltage_target,
            bimorph8.channel_2_voltage_target,
            bimorph8.channel_3_voltage_target,
            bimorph8.channel_4_voltage_target,
            bimorph8.channel_5_voltage_target,
            bimorph8.channel_6_voltage_target,
            bimorph8.channel_7_voltage_target,
            bimorph8.channel_8_voltage_target
            ]
    elif channel_type == ChannelTypes.VTRGT_RBV:
        return [
            bimorph8.channel_1_voltage_target_readback_value,
            bimorph8.channel_2_voltage_target_readback_value,
            bimorph8.channel_3_voltage_target_readback_value,
            bimorph8.channel_4_voltage_target_readback_value,
            bimorph8.channel_5_voltage_target_readback_value,
            bimorph8.channel_6_voltage_target_readback_value,
            bimorph8.channel_7_voltage_target_readback_value,
            bimorph8.channel_8_voltage_target_readback_value
        ]
    
    elif channel_type == ChannelTypes.SHIFT:
        return [
            bimorph8.channel_1_shift,
            bimorph8.channel_2_shift,
            bimorph8.channel_3_shift,
            bimorph8.channel_4_shift,
            bimorph8.channel_5_shift,
            bimorph8.channel_6_shift,
            bimorph8.channel_7_shift,
            bimorph8.channel_8_shift
        ]
    
    elif channel_type == ChannelTypes.VOUT:
        return [
            bimorph8.channel_1_voltage_out,
            bimorph8.channel_2_voltage_out,
            bimorph8.channel_3_voltage_out,
            bimorph8.channel_4_voltage_out,
            bimorph8.channel_5_voltage_out,
            bimorph8.channel_6_voltage_out,
            bimorph8.channel_7_voltage_out,
            bimorph8.channel_8_voltage_out
        ]
    elif channel_type == ChannelTypes.VOUT_RBV:
        return [
            bimorph8.channel_1_voltage_out_readback_value,
            bimorph8.channel_2_voltage_out_readback_value,
            bimorph8.channel_3_voltage_out_readback_value,
            bimorph8.channel_4_voltage_out_readback_value,
            bimorph8.channel_5_voltage_out_readback_value,
            bimorph8.channel_6_voltage_out_readback_value,
            bimorph8.channel_7_voltage_out_readback_value,
            bimorph8.channel_8_voltage_out_readback_value
        ]
    elif channel_type == ChannelTypes.STATUS:
        return [
            bimorph8.channel_1_status,
            bimorph8.channel_2_status,
            bimorph8.channel_3_status,
            bimorph8.channel_4_status,
            bimorph8.channel_5_status,
            bimorph8.channel_6_status,
            bimorph8.channel_7_status,
            bimorph8.channel_8_status
        ]


def parsed_read(device):
    res = device.read()
    return res[device.name]['value']


def test_basic_read_write():
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    # test ONOFF (make sure to leave on...):
    bimorph.on_off.set(OnOff.OFF).wait()
    assert parsed_read(bimorph.on_off) == OnOff.OFF
    bimorph.on_off.set(OnOff.ON).wait()
    assert parsed_read(bimorph.on_off) == OnOff.ON

    # test OPMODE:
    bimorph.on_off.set(OnOff.ON).wait()

    bimorph.operation_mode.set(OperationMode.HI).wait()
    assert parsed_read(bimorph.operation_mode) == OperationMode.HI
    bimorph.operation_mode.set(OperationMode.NORMAL).wait()
    assert parsed_read(bimorph.operation_mode) == OperationMode.NORMAL
    bimorph.operation_mode.set(OperationMode.FAST).wait()
    assert parsed_read(bimorph.operation_mode) == OperationMode.FAST

