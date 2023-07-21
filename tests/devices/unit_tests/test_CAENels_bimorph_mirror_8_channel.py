from ophyd import EpicsSignal

from dodal.devices.bimorph_mirrors.CAENels_bimorph_mirror_8_channel import (
    CAENelsBimorphMirror8Channel,
)
from dodal.devices.bimorph_mirrors.CAENels_bimorph_mirror_0_channel import (
    ChannelAttribute,
    OnOff,
    OperationMode,
    Status,
)

import random
from functools import partial
from ophyd import Component, Device, EpicsSignal
from typing import Union

"""
Stuff that isn't tested:
    CHANNELS
    TEMPS
    RESETERR.PROC
    ERR
    C1:STATUS ... C8:STATUS
"""


def get_channels_by_attributes(
    bimorph8: CAENelsBimorphMirror8Channel, channel_attribute: ChannelAttribute
) -> list:
    """
    Just takes an 8-chanel bimorph and returns a list of relevant the channel components
    """
    if channel_attribute == ChannelAttribute.VTRGT:
        return [
            bimorph8.channel_1_voltage_target,
            bimorph8.channel_2_voltage_target,
            bimorph8.channel_3_voltage_target,
            bimorph8.channel_4_voltage_target,
            bimorph8.channel_5_voltage_target,
            bimorph8.channel_6_voltage_target,
            bimorph8.channel_7_voltage_target,
            bimorph8.channel_8_voltage_target,
        ]
    elif channel_attribute == ChannelAttribute.VTRGT_RBV:
        return [
            bimorph8.channel_1_voltage_target_readback_value,
            bimorph8.channel_2_voltage_target_readback_value,
            bimorph8.channel_3_voltage_target_readback_value,
            bimorph8.channel_4_voltage_target_readback_value,
            bimorph8.channel_5_voltage_target_readback_value,
            bimorph8.channel_6_voltage_target_readback_value,
            bimorph8.channel_7_voltage_target_readback_value,
            bimorph8.channel_8_voltage_target_readback_value,
        ]

    elif channel_attribute == ChannelAttribute.SHIFT:
        return [
            bimorph8.channel_1_shift,
            bimorph8.channel_2_shift,
            bimorph8.channel_3_shift,
            bimorph8.channel_4_shift,
            bimorph8.channel_5_shift,
            bimorph8.channel_6_shift,
            bimorph8.channel_7_shift,
            bimorph8.channel_8_shift,
        ]

    elif channel_attribute == ChannelAttribute.VOUT:
        return [
            bimorph8.channel_1_voltage_out,
            bimorph8.channel_2_voltage_out,
            bimorph8.channel_3_voltage_out,
            bimorph8.channel_4_voltage_out,
            bimorph8.channel_5_voltage_out,
            bimorph8.channel_6_voltage_out,
            bimorph8.channel_7_voltage_out,
            bimorph8.channel_8_voltage_out,
        ]
    elif channel_attribute == ChannelAttribute.VOUT_RBV:
        return [
            bimorph8.channel_1_voltage_out_readback_value,
            bimorph8.channel_2_voltage_out_readback_value,
            bimorph8.channel_3_voltage_out_readback_value,
            bimorph8.channel_4_voltage_out_readback_value,
            bimorph8.channel_5_voltage_out_readback_value,
            bimorph8.channel_6_voltage_out_readback_value,
            bimorph8.channel_7_voltage_out_readback_value,
            bimorph8.channel_8_voltage_out_readback_value,
        ]
    elif channel_attribute == ChannelAttribute.STATUS:
        return [
            bimorph8.channel_1_status,
            bimorph8.channel_2_status,
            bimorph8.channel_3_status,
            bimorph8.channel_4_status,
            bimorph8.channel_5_status,
            bimorph8.channel_6_status,
            bimorph8.channel_7_status,
            bimorph8.channel_8_status,
        ]


def get_8_channel_values(
    bimorph: CAENelsBimorphMirror8Channel, channel_attribute: ChannelAttribute
) -> list:
    """
    Reads al 8 channels from bimorph of specifical channel type.
    """
    values = []
    for channel in get_channels_by_attributes(bimorph, channel_attribute):
        values.append(parsed_read(channel))
    return values


get_all_voltage_out_readback_values = partial(
    get_8_channel_values, channel_attribute=ChannelAttribute.VOUT_RBV
)


def wait_for_signal(
    signal: EpicsSignal,
    value,
    timeout: float = 10.0,
    sleep_time: float = 0.1,
    signal_range: Union[list, None] = None,
    wait_message: Union[str, None] = None,
) -> None:
    """
    Waits for signal to display given value. By default, times out after 10.0 seconds.

    If signal_range is given, an exception will be raised if currently read value from signal is outside of this.

    If a wait_message is given, this will be printed every time the function waits.
    """
    import time

    stamp = time.time()
    res = signal.read()[signal.name]["value"]
    while res != value:
        if wait_message is not None:
            print(wait_message)
        res = signal.read()[signal.name]["value"]
        if signal_range is not None:
            if res not in signal_range:
                raise Exception(
                    f"Out of range: {signal} showing {res} out or range {signal_range}"
                )
        if time.time() - stamp > timeout:
            raise Exception(f"Timeout: waiting for {signal} to show {value}")
        time.sleep(sleep_time)


wait_till_idle = partial(wait_for_signal, value=0, signal_range={0, 1})
wait_till_busy = partial(wait_for_signal, value=1, signal_range={0, 1})


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
    return res[signal.name]["value"]


def protected_set(wait_signal: EpicsSignal, signal: EpicsSignal, value) -> None:
    """
    Parses dict from Device.read to get value
    """
    wait_till_idle(wait_signal)
    signal.set(value).wait()
    wait_till_busy(wait_signal)


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
    """
    Tests that ONOFF is correctly setup to be read and set to.
    """
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    protected_set(bimorph.on_off, OnOff.OFF)
    assert parsed_read(bimorph.on_off) == OnOff.OFF
    protected_set(bimorph.on_off, OnOff.ON)
    assert parsed_read(bimorph.on_off) == OnOff.ON


def test_operation_mode_read_write():
    """
    Tests that OPMODE is correctly setup to be read and set to.
    Tests that the OnOff Enum has correct values corresponding to op modes.
    Tests that all three opmodes can be accessed.
    """
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    protected_set(bimorph.operation_mode, OperationMode.HI)
    assert parsed_read(bimorph.operation_mode_readback_value) == OperationMode.HI
    protected_set(bimorph.operation_mode, OperationMode.NORMAL)
    assert parsed_read(bimorph.operation_mode_readback_value) == OperationMode.NORMAL
    protected_set(bimorph.operation_mode, OperationMode.FAST)
    assert parsed_read(bimorph.operation_mode_readback_value) == OperationMode.FAST


def test_status():
    """
    Tests G0:STATUS is correctly set up to read from.

    I don't actually know if the way I'm testing this really works...
    """
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    assert bimorph.status.read()[bimorph.status.name]["value"] == Status.IDLE

    protected_set(bimorph.channel_1_voltage_out, 10.0)

    assert bimorph.status.read()[bimorph.status.name]["value"] == Status.BUSY


def test_all_shift():
    """
    Tests that ALLSHIFT is correctly setup to be read and set to.
    Tests VOUT is correctly setup to be read from.
    """
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    test_shift = round(random.random() * 30, 1) + 1
    current_voltages = get_all_voltage_out_readback_values(bimorph)

    protected_set(bimorph.all_shift, test_shift)
    assert parsed_read(bimorph.all_shift) == test_shift

    new_voltages = get_all_voltage_out_readback_values(bimorph)
    assert all(
        [
            voltpair[1] == voltpair[0] + test_shift
            for voltpair in zip(current_voltages, new_voltages)
        ]
    )


def test_all_volt():
    """
    Tests that ALLVOLT is correctly set up to be read and set to.
    Tests that VOUT_RBV is correctly set up to beread from.
    """
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    for i in range(3):
        # do it a few times in case the random number was the preexisting voltages:
        test_all_volt_value = random.randint(1, 30)
        protected_set(bimorph.all_volt, test_all_volt_value)
        assert all(
            [
                voltage == test_all_volt_value
                for voltage in get_all_voltage_out_readback_values(bimorph)
            ]
        )


def test_voltage_target():
    """
    Tests that VTRGT is correctly set up to be read and set to.
    Tests that VTRGT_RBV is correctly set up to be read and set to.
    Tests that VOUT_RBV is set up correctly to be read and set to.
    """
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    voltage_target_list = get_channels_by_attributes(bimorph, ChannelAttribute.VTRGT)
    voltage_target_readback_list = get_channels_by_attributes(bimorph, ChannelAttribute.VTRGT_RBV)

    # To make sure we don't happen to choose the current voltages, do twice:
    for i in range(2):
        target_voltages = [round(random.random() * 10, 1) for i in range(8)]

        for index, voltage_target_signal in enumerate(voltage_target_list):
            protected_set(voltage_target_signal, target_voltages[index])
        # breakpoint()

        assert all(
            [
                parsed_read(voltage_target_readback_list[i]) == target_voltages[i]
                for i in range(len(target_voltages))
            ]
        )

        protected_set(bimorph.all_target_proc, 1)

        new_voltages = get_all_voltage_out_readback_values(bimorph)

        assert all(
            [
                voltage == target_voltage
                for voltage, target_voltage in zip(new_voltages, target_voltages)
            ]
        )


def test_shift():
    """
    Test SHIFT if set up correctly to read and set to.
    """
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    shift_list = get_channels_by_attributes(bimorph, ChannelAttribute.SHIFT)

    shifts = [round(random.random() * 30 + 1) for i in range(8)]

    current_voltages = get_all_voltage_out_readback_values(bimorph)

    for shift, shift_signal in zip(shifts, shift_list):
        protected_set(shift_signal, shift)

    new_voltages = get_all_voltage_out_readback_values(bimorph)

    assert all(
        [
            new_voltage == old_voltage + shift
            for new_voltage, old_voltage, shift in zip(
                new_voltages, current_voltages, shifts
            )
        ]
    )


def test_voltage_out():
    """
    Tests VOUT is set up correctly to read and set to.
    """
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    voltage_out_list = get_channels_by_attributes(bimorph, ChannelAttribute.VOUT)

    for i in range(2):
        target_voltages = [round(random.random() * 10, 1) for i in range(8)]

        for index, voltage_out_signal in enumerate(voltage_out_list):
            protected_set(voltage_out_signal, target_voltages[index])

        assert all(
            [
                parsed_read(voltage_out_list[i]) == target_voltages[i]
                for i in range(len(target_voltages))
            ]
        )

        new_voltages = get_all_voltage_out_readback_values(bimorph)

        assert all(
            [
                voltage == target_voltage
                for voltage, target_voltage in zip(new_voltages, target_voltages)
            ]
        )


def test_get_channels_by_attribute():
    """
    Tests the bimorph's get_channels_by_attribute method.
    """
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.wait_for_connection()

    for channel_attribute in list(ChannelAttribute):
        channel1_list = bimorph.get_channels_by_attribute(channel_attribute)
        channel2_list = get_channels_by_attributes(bimorph, channel_attribute)

        print(f"channel1_list: {channel1_list}\nchannel2_list: {channel2_list}")

        assert all(
            [
                channel_1 == channel_2
                for channel_1, channel_2 in zip(channel1_list, channel2_list)
            ]
        )
