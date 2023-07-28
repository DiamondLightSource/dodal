from enum import Enum, IntEnum

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO

import time
from typing import Union

from functools import partial


class ChannelAttribute(Enum):
    VTRGT = ("VTRGT",)
    VTRGT_RBV = ("VTRGT_RBV",)
    SHIFT = ("SHIFT",)
    VOUT = ("VOUT",)
    VOUT_RBV = ("VOUT_RBV",)
    STATUS = "STATUS"


class OnOff(IntEnum):
    ON = (1,)
    OFF = 0


class OperationMode(IntEnum):
    HI = (0,)
    NORMAL = (1,)
    FAST = 2


class Status(IntEnum):
    IDLE = (0,)
    BUSY = (1,)
    ERR = 2


class CAENelsBimorphMirrorInterface(Device):
    """
    Class defining interface for Bimorph Mirrors. Base class of X-channel bimorphs.

    Not implemented:
        TARGETLISTCMD.PROC
        HYSTERESISLISTCMD.PROC
        TARGETWIPE.PROC
        HYSTERESISWIPE.PROC
        TARGETLIST (Component?)
        HYSTERESISLIST (Component?)
    """

    # Uses OnOff Enum:
    on_off: EpicsSignal = Component(EpicsSignal, "ONOFF")
    all_target_proc: EpicsSignal = Component(EpicsSignal, "ALLTRGT.PROC")
    # Uses OperationMode Enum:
    operation_mode: EpicsSignal = Component(EpicsSignal, "OPMODE")
    all_shift: EpicsSignal = Component(EpicsSignal, "ALLSHIFT")
    all_volt: EpicsSignal = Component(EpicsSignal, "ALLVOLT")
    operation_mode_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "OPMODE_RBV"
    )
    # Basically just the number of channels:
    channels: EpicsSignalRO = Component(EpicsSignalRO, "CHANNELS")
    status: EpicsSignalRO = Component(EpicsSignalRO, "STATUS")
    board_temperature: EpicsSignalRO = Component(EpicsSignalRO, "TEMPS")
    # PV suffix RESETERR.PROC, ERR, might be confusing. Errors come through
    # ..:BUSY kinda:
    reset_alarms: EpicsSignal = Component(EpicsSignal, "RESETERR.PROC")
    alarm_status: EpicsSignalRO = Component(EpicsSignalRO, "ERR")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Lists of channels for easy access:
        self._voltage_target_channels: list = []
        self._voltage_target_readback_value_channels: list = []
        self._shift_channels: list = []
        self._voltage_out_channels: list = []
        self._voltage_out_readback_value_channels: list = []
        self._status_channels: list = []

        # because self.status is compiled in a signal at instantiation, these have to be define in __init__:
        self.wait_till_idle = partial(
            self.wait_for_signal_value,
            self.status,
            Status.IDLE,
            signal_range=[Status.IDLE, Status.BUSY],
        )
        self.wait_till_busy = partial(
            self.wait_for_signal_value,
            self.status,
            Status.BUSY,
            signal_range=[Status.IDLE, Status.BUSY],
        )

    def wait_for_signal_value(
        self,
        signal: EpicsSignal,
        value,
        timeout: float = 10.0,
        sleep_time: float = 0.1,
        signal_range: Union[list, None] = None,
    ):
        """Wait for a signal to display given value. Default to polling time of 0.1 seconds, and timeout after 10.0.

        If signal_range is non-none, an exception will be raised if the signal value does not exist in signal_range list.
        """
        stamp = time.time()
        res = signal.read()[signal.name]["value"]

        while res != value:
            if signal_range is not None:
                if res not in signal_range:
                    raise Exception(
                        f"Out of range: {signal} showing {res} not in {signal_range}"
                    )

            if time.time() - stamp > timeout:
                raise Exception(f"Timeout waiting for {signal} to show {value}")

            time.sleep(sleep_time)

            res = signal.read()[signal.name]["value"]

    def protected_read(self, signal: EpicsSignal):
        """Waits for bimorph to be idle, then reads from signal.

        Args:
            signal: The signal to be read from

        Returns:
            A dictionary contaning value(s) read and other relevant data
        """
        self.wait_till_idle()
        return signal.read()

    def protected_set(self, signal: EpicsSignal, value):
        """Waits for bimorph to be idle, writes to signal, then waits for busy signal

        Args:
            signal: Signal to be written to
            value: Value to be written to signal
        """
        self.wait_till_idle()
        signal.set(value)
        self.wait_till_busy()

    def parsed_protected_read(self, signal: EpicsSignal):
        """Calls waits till idle then reads from signal and parses output for value.

        Args:
            signal: The signal to be read from

        Returns:
            A value read from the signal
        """
        res = self.protected_read(signal)
        return res[signal.name]["value"]

    def get_channels_by_attribute(self, channel_attribute: ChannelAttribute) -> list:
        """Takes an attribute and returns a list of Signals that share that attribute across all channels.

        Args:
            channel_attribute: A ChannelAttribute enum representing the grouping of signals to be returned.
                eg: ChannelAttribute.VOUT would yield a list of objects representing [C1:VOUT, C2:VOUT, ..., CX:VOUT]
                for an X-channel bimorph

        Returns:
            A list containing X Signals where X is the number of channels of the bimorph.
        """
        if channel_attribute == ChannelAttribute.VTRGT:
            return self._voltage_target_channels

        elif channel_attribute == ChannelAttribute.VTRGT_RBV:
            return self._voltage_target_readback_value_channels

        elif channel_attribute == ChannelAttribute.SHIFT:
            return self._shift_channels

        elif channel_attribute == ChannelAttribute.VOUT:
            return self._voltage_out_channels

        elif channel_attribute == ChannelAttribute.VOUT_RBV:
            return self._voltage_out_readback_value_channels

        elif channel_attribute == ChannelAttribute.STATUS:
            return self._status_channels

    def read_from_all_channels_by_attribute(
        self, channel_attribute: ChannelAttribute
    ) -> list:
        """Takes an attribuet and returns a list of values read from all signals sharing that attribute.

        Args:
            channel_attribute: A ChannelAttribute enum representing the grouping of signals to be returned.
                eg: ChannelAttribute.VOUT would yield a list of objects representing [C1:VOUT, C2:VOUT, ..., CX:VOUT]
                for an X-channel bimorph            channel_attribute: attribute grouping


        Returns:
            A list of values read from X signals related to the given attribute, where X is the numebr of channels in the bimorph.
        """
        channels = self.get_channels_by_attribute(channel_attribute)

        return [self.parsed_protected_read(channel) for channel in channels]
    
    def write_to_all_channels_by_attribute(self, channel_attribute: ChannelAttribute, values: list):
        """Writes given values to signals grouped by given attribute.
        
        Args:
            channel_attribute: A ChannelAttribute enum representing the grouping of signals to be written to.
            values: A list of values of length equal to the number of channels of the bimorph
        """
        channels = self.get_channels_by_attribute(channel_attribute)

        for channel, value in zip(channels, values):
            self.protected_set(channel, value)

    def set_and_proc_target_voltages(self, target_voltages: list[int]):
        """Sets VTRGT channels ot values in target_voltages, and sets off ALLTRGT.PROC
        
        Args:
            target_voltages: An array of length equal to number of channels, with 
                target_voltages[X] being set for channel_X_target_volage"""
        
        self.write_to_all_channels_by_attribute(ChannelAttribute.VTRGT,
                                                target_voltages)
        
        self.protected_set(self.all_target_proc, 1)
