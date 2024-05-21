import time
from enum import Enum, IntEnum
from functools import partial
from typing import Any, Union

from bluesky.protocols import Movable
from ophyd import Component, Device, EpicsSignal, EpicsSignalRO
from ophyd.status import StatusBase, SubscriptionStatus

from dodal.devices.status import await_value


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


class CAENelsBimorphMirrorInterface(Device, Movable):
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
        value: Any,
        timeout: float = 10.0,
        sleep_time: float = 0.1,
        signal_range: Union[list, None] = None,
    ):
        """Wait for a signal to display given value. Default to polling time of 0.1 seconds, and timeout after 10.0.
        If signal_range is non-none, an exception will be raised if the signal value does not exist in signal_range list.

        Args:
            signal: The signal to be read from
            value: Once this value is read from signal, the function will return
            timeout: Time before an exception is raised in seconds (default 10.0)
            sleep_time: Polling time in seconds (default 0.1)
            signal_range: Range of allowed values. If value outside of this is read, an exception will be thrown
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
        await_value(self.status, Status.IDLE).wait()
        return signal.read()

    def protected_set(self, signal: EpicsSignal, value) -> SubscriptionStatus:
        """Waits for bimorph to be idle, writes to signal.

        Args:
            signal: Signal to be written to
            value: Value to be written to signal

        Returns:
            A SubscriptionStatus to track that the bimorph has entered its
                post-operation idle state.
        """
        await_value(self.status, Status.IDLE).wait()
        status = signal.set(value)
        await_value(self.status, Status.BUSY).wait()
        return status & await_value(self.status, Status.IDLE)

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
        """Takes an attribute and returns a list of values read from all signals sharing that attribute.

        Args:
            channel_attribute: A ChannelAttribute enum representing the grouping of signals to be returned.
                eg: ChannelAttribute.VOUT would yield a list of objects representing [C1:VOUT, C2:VOUT, ..., CX:VOUT]
                for an X-channel bimorph            channel_attribute: attribute grouping


        Returns:
            A list of values read from X signals related to the given attribute, where X is the numebr of channels in the bimorph.
        """
        channels = self.get_channels_by_attribute(channel_attribute)

        return [self.parsed_protected_read(channel) for channel in channels]

    def write_to_all_channels_by_attribute(
        self, channel_attribute: ChannelAttribute, values: list
    ) -> SubscriptionStatus:
        """Writes given values to signals grouped by given attribute.

        Args:
            channel_attribute: A ChannelAttribute enum representing the grouping of signals to be written to.
            values: A list of values of length equal to the number of channels of the bimorph

        Returns:
            A SubscriptionStatus object tracking completion of operations
        """
        channels = self.get_channels_by_attribute(channel_attribute)

        status = StatusBase()
        status.set_finished()

        for i, (channel, value) in enumerate(zip(channels, values)):
            status &= self.protected_set(channel, value)

            if i >= len(channels) - 1:
                return status

            status.wait()
        return status

    def set_and_proc_target_voltages(
        self, target_voltages: list[float]
    ) -> SubscriptionStatus:
        """Sets VTRGT channels ot values in target_voltages, and sets off ALLTRGT.PROC

        Args:
            target_voltages: An array of length equal to number of channels, with
                target_voltages[X] being set for channel_X_target_volage

        Returns:
            A SubscriptionStatus object tracking completion of operations
        """

        status = self.write_to_all_channels_by_attribute(
            ChannelAttribute.VTRGT, target_voltages
        )

        status.wait()

        return status & self.protected_set(self.all_target_proc, 1)
    
    def diff_set_and_proc_target_voltages(
        self, target_voltages: list[float]
    ) -> SubscriptionStatus:
        """Sets VTRGT channels to values in target_voltages efficiently by diff

        Checks for diff between VTRGT_RBV and target_voltages, then writes to VTRGT for
        each difference.

        Args:
            target_voltages: An array of length equal to number of channels, with
                target_voltages[X] being set for channel_X_target_voltage if 
                channel_x_target_voltage_readback_value != target_voltage[x]
        
        Returns:
            A SubscriptionStatus object tracking completion of operations
        """

        voltage_target_rbvs = self.read_from_all_channels_by_attribute(ChannelAttribute.VTRGT_RBV)

        status = StatusBase()
        status.set_finished()

        for i, channel in enumerate(self.get_channels_by_attribute(ChannelAttribute.VTRGT)):
            if target_voltages[i] != voltage_target_rbvs[i]:
                status &= self.protected_set(channel, target_voltages[i])
            
            status.wait()
        return status


    def set(self, target_voltages: list[float], settle_time = 0) -> SubscriptionStatus:
        """Sets each voltage channel to equivalent value in target_voltages.

        Args:
            target_voltages: An array of length equal to number of channels
            settle_time: Pause in seconds after action completes
        Returns:
            A SubscriptionStatus object tracking completion of operations
        """

        status = self.diff_set_and_proc_target_voltages(target_voltages_)
        settler = StatusBase(settle_time = settle_time)
        settler.set_finished()
        return status & settler 
