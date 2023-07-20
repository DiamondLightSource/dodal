from enum import IntEnum

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO

class OnOff(IntEnum):
    ON = 1,
    OFF = 0


class OperationMode(IntEnum):
    HI = 0,
    NORMAL = 1,
    FAST = 2

class Status(IntEnum):
    IDLE = 0,
    BUSY = 1,
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