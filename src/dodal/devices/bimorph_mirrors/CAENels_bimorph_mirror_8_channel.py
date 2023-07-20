from .CAENels_bimorph_mirror_7_channel import CAENelsBimorphMirror7Channel

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO


class CAENelsBimorphMirror8Channel(CAENelsBimorphMirror7Channel):
    """
    Class representing a CAENels 8-Channel Bimorph Mirror.

    Not implemented:
        TARGETLISTCMD.PROC
        HYSTERESISLISTCMD.PROC
        TARGETWIPE.PROC
        HYSTERESISWIPE.PROC
        TARGETLIST (Component?)
        HYSTERESISLIST (Component?)
    """


    channel_8_voltage_target: EpicsSignal = Component(EpicsSignal, "C8:VTRGT")


    channel_8_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C8:VTRGT_RBV"
    )

    channel_8_shift: EpicsSignal = Component(EpicsSignal, "C8:SHIFT")

    channel_8_voltage_out: EpicsSignal = Component(EpicsSignal, "C8:VOUT")

    channel_8_voltage_out_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C8:VOUT_RBV"
    )

    channel_8_status: EpicsSignalRO = Component(EpicsSignalRO, "C8:STATUS")
