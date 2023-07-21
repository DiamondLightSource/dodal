from enum import Enum, IntEnum

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO


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


class CAENelsBimorphMirror0Channel(Device):
    """
    Class representing a CAENels 0-Channel Bimorph Mirror. Base class of X-channel bimorphs.

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
        pass
