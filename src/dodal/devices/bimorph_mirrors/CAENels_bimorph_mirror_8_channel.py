from .CAENels_bimorph_mirror_7_channel import CAENelsBimorphMirror7Channel

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO


class CAENelsBimorphMirror8Channel(CAENelsBimorphMirror7Channel):
    """
    Class representing a CAENels 8-Channel Bimorph Mirror.

    Adds 8th channel to 7 inherited.

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


    # lists of channels for easy access
    # there must be a nicer way to do this:
    _voltage_target_channels = CAENelsBimorphMirror7Channel._voltage_target_channels.copy()
    
    _voltage_target_channels.extend([
        channel_8_voltage_target,
    ])

    _voltage_target_readback_value_channels = CAENelsBimorphMirror7Channel._voltage_target_readback_value_channels.copy()
    
    _voltage_target_readback_value_channels.extend([
        channel_8_voltage_target_readback_value,
    ])

    _shift_channels = CAENelsBimorphMirror7Channel._shift_channels.copy()

    _shift_channels.extend([
        channel_8_shift,
    ])

    _voltage_out_channels = CAENelsBimorphMirror7Channel._voltage_out_channels.copy()
    
    _voltage_out_channels.extend([
        channel_8_voltage_out,
    ])

    _voltage_out_readback_value_channels = CAENelsBimorphMirror7Channel._voltage_out_readback_value_channels.copy()
    
    _voltage_out_readback_value_channels.extend([
        channel_8_voltage_out_readback_value,
    ])
    
    _status_channels = CAENelsBimorphMirror7Channel._status_channels.copy()
    
    _status_channels.extend([
        channel_8_status,
    ])
