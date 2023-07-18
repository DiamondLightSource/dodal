import pytest
from bluesky import RunEngine
from ophyd import EpicsSignal

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

def get_channels(bimorph8: CAENelsBimorphMirror8Channel, channel_type: ChannelTypes) -> list:
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
    
def get_all_voltage_out_readback_values(bimorph: CAENelsBimorphMirror8Channel) -> list[float]:
    """
    Function to returning all VOUT_RBV values from given bimorph as a list
    """
    current_voltages = []
    for channel in get_channels(bimorph, ChannelTypes.VOUT_RBV):
        voltage = parsed_read(channel)
        current_voltages.append(voltage)
    return current_voltages


def wait_for_signal(signal: EpicsSignal, value, timeout: float=10.0, sleep_time: float=0.1, signal_range: list = None, wait_message: str = None) -> None:
    """
    Waits for signal to display given value. By default, times out after 10.0 seconds.

    If signal_range is given, an exception will be raised if currently read value from signal is outside of this.

    If a wait_message is given, this will be printed every time the function waits.
    """
    import time
    stamp=time.time()
    res = signal.read()[signal.name]['value']
    while res != value:
        if wait_message is not None:
            print(wait_message)
        res = signal.read()[signal.name]['value']
        if signal_range is not None:
            if res not in signal_range:
                raise Exception(f"Out of range: {signal} showing {res} out or range {signal_range}")
        if time.time() - stamp > timeout:
            raise Exception(f"Timeout: waiting for {signal} to show {value}")
        time.sleep(sleep_time)


from functools import partial
wait_till_idle = partial(wait_for_signal, value=0, signal_range={0,1})
wait_till_busy = partial(wait_for_signal, value=1, signal_range={0,1})


def protected_read(wait_signal: EpicsSignal, signal: EpicsSignal):
    """
    Reads from signal, but safely...
    """
    wait_till_idle(wait_signal)
    return signal.read()

def parsed_read(wait_signal: EpicsSignal, signal: EpicsSignal):
    """
    Writes to signal, but safely...
    """
    res = protected_read(wait_signal, signal)
    return res[signal.name]['value']

def protected_set(wait_signal: EpicsSignal, component: EpicsSignal, value) -> None:
    """
    Parses dict from Device.read to get value
    """
    print(f"Write {value} to {component}")
    wait_till_idle(wait_signal)
    print(f"Written {value} to {component}")
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
    protected_set(bimorph.operation_mode, OperationMode.HI)
    assert parsed_read(bimorph.operation_mode_readback_value) == OperationMode.HI
    protected_set(bimorph.operation_mode, OperationMode.NORMAL)
    assert parsed_read(bimorph.operation_mode_readback_value) == OperationMode.NORMAL
    protected_set(bimorph.operation_mode, OperationMode.FAST)
    assert parsed_read(bimorph.operation_mode_readback_value) == OperationMode.FAST

def test_all_shift():
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    # test ALLSHIFT:
    import random
    test_shift = random.randint(1,30) 

    current_voltages = get_all_voltage_out_readback_values(bimorph)
    protected_set(bimorph.all_shift, test_shift)
    assert parsed_read(bimorph.all_shift) == test_shift 
    new_voltages = get_all_voltage_out_readback_values(bimorph)
    assert all([voltpair[1] == voltpair[0]+test_shift for
                voltpair in zip(current_voltages, new_voltages)])

def test_all_volt():
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    # test ALLVOLT:
    import random
    for i in range(3): 
        # do it a few times in case the random number was the preexisting voltages:
        test_all_volt_value = random.randint(1,30)
        protected_set(bimorph.all_volt, test_all_volt_value)
        assert all([voltage == test_all_volt_value for voltage in get_all_voltage_out_readback_values(bimorph)])