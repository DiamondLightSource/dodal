import random
from functools import partial
from typing import Union

import pytest
from bluesky import RunEngine
from bluesky.plan_stubs import mv
from ophyd import Component, Device, EpicsSignal

from dodal.devices.bimorph_mirrors.CAENels_bimorph_mirror_8_channel import (
    CAENelsBimorphMirror8Channel,
)
from dodal.devices.bimorph_mirrors.CAENels_bimorph_mirror_interface import (
    ChannelAttribute,
    OnOff,
    OperationMode,
    Status,
)

"""
Stuff that isn't tested:
    CHANNELS
    TEMPS
    RESETERR.PROC
    ERR
    C1:STATUS ... C8:STATUS
"""


def get_bimorph(name="bimorph", prefix="BL02J-EA-IOC-97:G0:"):
    bimorph = CAENelsBimorphMirror8Channel(name=name, prefix=prefix)
    bimorph.wait_for_connection()
    return bimorph


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
    return [None for _ in range(8)]


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
    device_busy: EpicsSignal = Component(EpicsSignal, "STATUS")


busy_signal = BusySignalGetter(name="busy_signal", prefix="BL02J-EA-IOC-97:G0:")
parsed_read = partial(parsed_read, busy_signal.device_busy)
protected_set = partial(protected_set, busy_signal.device_busy)


# ACTUAL TEST CASES:


@pytest.mark.bimorph
def test_on_off_read_write():
    """
    Tests that ONOFF is correctly setup to be read and set to.
    """
    bimorph = get_bimorph()

    protected_set(bimorph.on_off, OnOff.OFF)
    assert parsed_read(bimorph.on_off) == OnOff.OFF
    protected_set(bimorph.on_off, OnOff.ON)
    assert parsed_read(bimorph.on_off) == OnOff.ON


@pytest.mark.bimorph
def test_operation_mode_read_write():
    """
    Tests that OPMODE is correctly setup to be read and set to.
    Tests that the OnOff Enum has correct values corresponding to op modes.
    Tests that all three opmodes can be accessed.
    """
    bimorph = get_bimorph()

    protected_set(bimorph.operation_mode, OperationMode.HI)
    assert parsed_read(bimorph.operation_mode_readback_value) == OperationMode.HI
    protected_set(bimorph.operation_mode, OperationMode.NORMAL)
    assert parsed_read(bimorph.operation_mode_readback_value) == OperationMode.NORMAL
    protected_set(bimorph.operation_mode, OperationMode.FAST)
    assert parsed_read(bimorph.operation_mode_readback_value) == OperationMode.FAST


@pytest.mark.bimorph
def test_status():
    """
    Tests G0:STATUS is correctly set up to read from.

    I don't actually know if the way I'm testing this really works...
    """
    bimorph = get_bimorph()

    assert bimorph.status.read()[bimorph.status.name]["value"] == Status.IDLE

    protected_set(bimorph.channel_1_voltage_out, 10.0)

    assert bimorph.status.read()[bimorph.status.name]["value"] == Status.BUSY


@pytest.mark.bimorph
def test_all_shift():
    """
    Tests that ALLSHIFT is correctly setup to be read and set to.
    Tests VOUT is correctly setup to be read from.
    """
    bimorph = get_bimorph()

    test_shift = round(random.random() * 30, 1) + 1
    current_voltages = get_all_voltage_out_readback_values(bimorph)

    protected_set(bimorph.all_shift, test_shift)
    assert parsed_read(bimorph.all_shift) == test_shift

    new_voltages = get_all_voltage_out_readback_values(bimorph)
    assert all(
        voltpair[1] == voltpair[0] + test_shift
        for voltpair in zip(current_voltages, new_voltages)
    )


@pytest.mark.bimorph
def test_all_volt():
    """
    Tests that ALLVOLT is correctly set up to be read and set to.
    Tests that VOUT_RBV is correctly set up to beread from.
    """
    bimorph = get_bimorph()

    for i in range(3):
        # do it a few times in case the random number was the preexisting voltages:
        test_all_volt_value = random.randint(1, 30)
        protected_set(bimorph.all_volt, test_all_volt_value)
        assert all(
            voltage == test_all_volt_value
            for voltage in get_all_voltage_out_readback_values(bimorph)
        )


@pytest.mark.bimorph
def test_voltage_target():
    """
    Tests that VTRGT is correctly set up to be read and set to.
    Tests that VTRGT_RBV is correctly set up to be read and set to.
    Tests that VOUT_RBV is set up correctly to be read and set to.
    """
    bimorph = get_bimorph()

    voltage_target_list = get_channels_by_attributes(bimorph, ChannelAttribute.VTRGT)
    voltage_target_readback_list = get_channels_by_attributes(
        bimorph, ChannelAttribute.VTRGT_RBV
    )

    # To make sure we don't happen to choose the current voltages, do twice:
    for i in range(2):
        target_voltages = [round(random.random() * 10, 1) for i in range(8)]

        for index, voltage_target_signal in enumerate(voltage_target_list):
            protected_set(voltage_target_signal, target_voltages[index])
        # breakpoint()

        assert all(
            parsed_read(voltage_target_readback_list[i]) == target_voltages[i]
            for i in range(len(target_voltages))
        )

        protected_set(bimorph.all_target_proc, 1)

        new_voltages = get_all_voltage_out_readback_values(bimorph)

        assert all(
            voltage == target_voltage
            for voltage, target_voltage in zip(new_voltages, target_voltages)
        )


@pytest.mark.bimorph
def test_shift():
    """
    Test SHIFT if set up correctly to read and set to.
    """
    bimorph = get_bimorph()

    shift_list = get_channels_by_attributes(bimorph, ChannelAttribute.SHIFT)

    shifts = [round(random.random() * 30 + 1) for i in range(8)]

    current_voltages = get_all_voltage_out_readback_values(bimorph)

    for shift, shift_signal in zip(shifts, shift_list):
        protected_set(shift_signal, shift)

    new_voltages = get_all_voltage_out_readback_values(bimorph)

    assert all(
        new_voltage == old_voltage + shift
        for new_voltage, old_voltage, shift in zip(
            new_voltages, current_voltages, shifts
        )
    )


@pytest.mark.bimorph
def test_voltage_out():
    """
    Tests VOUT is set up correctly to read and set to.
    """
    bimorph = get_bimorph()

    voltage_out_list = get_channels_by_attributes(bimorph, ChannelAttribute.VOUT)

    for i in range(2):
        target_voltages = [round(random.random() * 10, 1) for i in range(8)]

        for index, voltage_out_signal in enumerate(voltage_out_list):
            protected_set(voltage_out_signal, target_voltages[index])

        assert all(
            parsed_read(voltage_out_list[i]) == target_voltages[i]
            for i in range(len(target_voltages))
        )

        new_voltages = get_all_voltage_out_readback_values(bimorph)

        assert all(
            voltage == target_voltage
            for voltage, target_voltage in zip(new_voltages, target_voltages)
        )


@pytest.mark.bimorph
def test_get_channels_by_attribute():
    """
    Tests the bimorph's get_channels_by_attribute method.
    """
    bimorph = get_bimorph()

    for channel_attribute in list(ChannelAttribute):
        channel1_list = bimorph.get_channels_by_attribute(channel_attribute)
        channel2_list = get_channels_by_attributes(bimorph, channel_attribute)

        print(f"channel1_list: {channel1_list}\nchannel2_list: {channel2_list}")

        assert all(
            channel_1 == channel_2
            for channel_1, channel_2 in zip(channel1_list, channel2_list)
        )


@pytest.mark.bimorph
def test_wait_for_signal_value():
    """
    Tests that bimorph's wait_for_signal_value works.

    I don't really know that these tests proves much...
    """
    bimorph = get_bimorph()

    protected_set(bimorph.channel_1_voltage_out, 10)
    bimorph.wait_for_signal_value(bimorph.status, 0)
    assert bimorph.status.read()[bimorph.status.name]["value"] == 0

    protected_set(bimorph.channel_1_voltage_out, 20)
    bimorph.wait_for_signal_value(bimorph.channel_1_voltage_out_readback_value, 20)
    assert (
        bimorph.channel_1_voltage_out_readback_value.read()[
            bimorph.channel_1_voltage_out_readback_value.name
        ]["value"]
        == 20
    )


@pytest.mark.bimorph
def test_wait_till_idle_and_busy():
    """
    Test to see if CAENelsBimorphMirrorInterface.wait_till_idle and .wait_till_busy work...

    I feel like to do this properly I need to do some clever async stuff, so this is fairly light.
    """
    bimorph = get_bimorph()

    test_voltage = round(random.random() * 30, 1) + 1
    bimorph.channel_1_voltage_out.set(test_voltage)
    bimorph.wait_till_busy()
    assert bimorph.status.read()[bimorph.status.name]["value"] == Status.BUSY
    bimorph.wait_till_idle()
    assert bimorph.status.read()[bimorph.status.name]["value"] == Status.IDLE


@pytest.mark.bimorph
def test_protected_read():
    """
    Tests if CAENelsBimorphMirrorInterface.protected_read works
    """
    bimorph = get_bimorph()

    test_voltage = round(random.random() * 30, 1) + 1

    protected_set(bimorph.channel_1_voltage_out, test_voltage)
    assert (
        bimorph.protected_read(bimorph.channel_1_voltage_out_readback_value)[
            bimorph.channel_1_voltage_out_readback_value.name
        ]["value"]
        == test_voltage
    )

    assert bimorph.status.read()[bimorph.status.name]["value"] == Status.IDLE


@pytest.mark.bimorph
def test_protected_set():
    """
    Tests CAENelsBimorphMirrorInterface.protected_set
    """
    bimorph = get_bimorph()

    test_voltage = round(random.random() * 30, 1) + 1

    status = bimorph.protected_set(bimorph.channel_1_voltage_out, test_voltage)
    status.wait()

    assert bimorph.status.read()[bimorph.status.name]["value"] == Status.IDLE
    assert parsed_read(bimorph.channel_1_voltage_out_readback_value) == test_voltage


@pytest.mark.bimorph
def test_parsed_protected_read():
    """
    Tests CAENelsBimorphMirrorInterface.parsed_protected_read
    """
    bimorph = get_bimorph()

    test_voltage = round(random.random() * 30, 1) + 1

    protected_set(bimorph.channel_1_voltage_out, test_voltage)
    assert (
        bimorph.parsed_protected_read(bimorph.channel_1_voltage_out_readback_value)
        == test_voltage
    )

    assert bimorph.status.read()[bimorph.status.name]["value"] == Status.IDLE


@pytest.mark.bimorph
def test_read_from_all_channels_by_attribute():
    """
    Tests CAENelsBimorphMirror8Channel.read_from_all_channels_by_attribute
    """
    bimorph = get_bimorph()

    voltage_out_list = get_channels_by_attributes(bimorph, ChannelAttribute.VOUT)

    target_voltages = [round(random.random() * 10, 1) for i in range(8)]

    for index, voltage_out_signal in enumerate(voltage_out_list):
        protected_set(voltage_out_signal, target_voltages[index])

    voltage_out_rbv_values = bimorph.read_from_all_channels_by_attribute(
        ChannelAttribute.VOUT_RBV
    )

    assert all(
        vout_rbv_value == target_voltage
        for vout_rbv_value, target_voltage in zip(
            voltage_out_rbv_values, target_voltages
        )
    )


@pytest.mark.bimorph
def test_write_to_all_channels_by_attribute():
    """
    Tests CAENelsBimorphMirror8Channel.write_to_all_channels_by_attribute
    """
    bimorph = get_bimorph()

    voltage_out_list = get_channels_by_attributes(bimorph, ChannelAttribute.VOUT)

    target_voltages = [round(random.random() * 10, 1) for i in range(8)]

    status = bimorph.write_to_all_channels_by_attribute(
        ChannelAttribute.VOUT, target_voltages
    )
    status.wait()

    assert all(
        parsed_read(voltage_out) == target_voltage
        for voltage_out, target_voltage in zip(voltage_out_list, target_voltages)
    )

    new_voltages = get_all_voltage_out_readback_values(bimorph)

    assert all(
        voltage == target_voltage
        for voltage, target_voltage in zip(new_voltages, target_voltages)
    )


@pytest.mark.bimorph
def test_set_and_proc_target_voltages():
    """
    Tests CAENelsBimorphMirror8Channel.set_and_proc_target_voltages
    """
    bimorph = get_bimorph()

    target_voltages = [round(random.random() * 10, 1) for i in range(8)]

    vout_rbv_list = get_channels_by_attributes(bimorph, ChannelAttribute.VOUT_RBV)

    voltage_target_rbv_list = get_channels_by_attributes(
        bimorph, ChannelAttribute.VTRGT_RBV
    )

    status = bimorph.set_and_proc_target_voltages(target_voltages)
    status.wait()

    assert all(
        parsed_read(vtrgt_rbv) == voltage
        for vtrgt_rbv, voltage in zip(voltage_target_rbv_list, target_voltages)
    )

    assert all(
        parsed_read(vout) == voltage
        for vout, voltage in zip(vout_rbv_list, target_voltages)
    )


@pytest.mark.bimorph
def test_set():
    """
    Tests CAENelsBimorphMirror8Channel.set
    """
    bimorph = get_bimorph()

    target_voltages = [round(random.random() * 10, 1) for i in range(8)]

    vout_rbv_list = get_channels_by_attributes(bimorph, ChannelAttribute.VOUT_RBV)

    voltage_target_rbv_list = get_channels_by_attributes(
        bimorph, ChannelAttribute.VTRGT_RBV
    )

    status = bimorph.set(target_voltages)
    status.wait()

    assert all(
        parsed_read(vtrgt_rbv) == voltage
        for vtrgt_rbv, voltage in zip(voltage_target_rbv_list, target_voltages)
    )

    assert all(
        parsed_read(vout) == voltage
        for vout, voltage in zip(vout_rbv_list, target_voltages)
    )


# This section test the bimorph in Bluesky plan contexts:


RE = RunEngine({})


@pytest.mark.bimorph
def test_move_plan():
    bimorph = get_bimorph()

    target_voltages = [round(random.random() * 10, 1) for i in range(8)]

    def move_plan(bimorph, target_voltages):
        yield from mv(bimorph, target_voltages)

    RE(move_plan(bimorph, target_voltages), print)

    new_voltages = get_all_voltage_out_readback_values(bimorph)

    assert all(
        voltage == target_voltage
        for voltage, target_voltage in zip(new_voltages, target_voltages)
    )
