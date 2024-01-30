from ophyd import Component, Device, EpicsSignal, EpicsSignalRO

from .CAENels_bimorph_mirror_7_channel import CAENelsBimorphMirror7Channel


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # lists of channels for easy access
        # there must be a nicer way to do this:

        self._voltage_target_channels.extend(
            [
                self.channel_8_voltage_target,
            ]
        )

        self._voltage_target_readback_value_channels.extend(
            [
                self.channel_8_voltage_target_readback_value,
            ]
        )

        self._shift_channels.extend(
            [
                self.channel_8_shift,
            ]
        )

        self._voltage_out_channels.extend(
            [
                self.channel_8_voltage_out,
            ]
        )

        self._voltage_out_readback_value_channels.extend(
            [
                self.channel_8_voltage_out_readback_value,
            ]
        )

        self._status_channels.extend(
            [
                self.channel_8_status,
            ]
        )
