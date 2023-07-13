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
def wait_till_idle(wait_signal):
    """
    Waits for wait_signal to be Idle.

    Interprets wait_signal as
        0: Idle
        1: Busy
        2: Error
    """
    import time
    while wait_signal.read()[wait_signal.name]['value'] !=0:
        print("waiting till idle...")
        time.sleep(0.1)

def wait_till_busy(wait_signal):
    """
    Waits for wait_signal to be Busy.
    
    This is because EPICS is slow enough that we need to wait for things to show as busy
    to be able to then wait for them to be Idle.

    Interprets wait_signal as
        0: Idle
        1: Busy
        2: Error
    """
    import time
    while wait_signal.read()[wait_signal.name]['value'] !=1:
        print("waiting till busy...")
        time.sleep(0.1)



def protected_read(wait_signal, device):
    """
    Reads from device, but safely...
    """
    wait_till_idle(wait_signal)
    return device.read()

def parsed_read(wait_signal, device):
    """
    Writes to device, but safely...
    """
    res = protected_read(wait_signal, device)
    return res[device.name]['value']

def protected_set(wait_signal, component, value):
    """
    Parses dict from Device.read to get value
    """
    print(f"Write {value} to {component}")
    wait_till_idle(wait_signal)
    component.set(value).wait()
    wait_till_busy(wait_signal)


from functools import partial
from ophyd import Component, Device, EpicsSignal

# Stupid ugly class to get the "Device Busy" signal from the bimorph controller
# Workaround because the architecture for this is weird and hard to implement
# in a unit test:
class BusySignalGetter(Device):
    device_busy: EpicsSignal = Component(EpicsSignal, "BUSY")
busy_signal = BusySignalGetter(name="busy_signal", prefix="BL02J-EA-IOC-97:")
parsed_read = partial(parsed_read, busy_signal.device_busy)
protected_set = partial(protected_set, busy_signal.device_busy)


# ACTUAL TEST CASES:



def test_on_off_read_write():
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    # test ONOFF (make sure to leave on...):
    protected_set(bimorph.on_off, OnOff.OFF)
    assert parsed_read(bimorph.on_off) == OnOff.OFF
    protected_set(bimorph.on_off, OnOff.ON)
    assert parsed_read(bimorph.on_off) == OnOff.ON

def test_operation_mode_read_write():
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    # test OPMODE:
    protected_set(bimorph.on_off, OnOff.ON)

    protected_set(bimorph.operation_mode, OperationMode.HI)
    assert parsed_read(bimorph.operation_mode) == OperationMode.HI
    protected_set(bimorph.operation_mode, OperationMode.NORMAL)
    assert parsed_read(bimorph.operation_mode) == OperationMode.NORMAL
    protected_set(bimorph.operation_mode, OperationMode.FAST)
    assert parsed_read(bimorph.operation_mode) == OperationMode.FAST

def test_all_shift():
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    # test ALLSHIFT:
    import random
    test_shift = random.randint(1,30) 

    def get_voltages(bimorph):
        current_voltages = []
        for channel in get_channels(bimorph, ChannelTypes.VOUT_RBV):
            voltage = parsed_read(channel)
            current_voltages.append(voltage)
        return current_voltages

    current_voltages = get_voltages(bimorph)
    protected_set(bimorph.all_shift, test_shift)
    assert parsed_read(bimorph.all_shift) == test_shift 
    new_voltages = get_voltages(bimorph)
    assert all([voltpair[1] == voltpair[0]+test_shift for
                voltpair in zip(current_voltages, new_voltages)])