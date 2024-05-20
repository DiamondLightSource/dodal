from ophyd import Component, EpicsSignal, EpicsSignalRO

from dodal.devices.bimorph_mirrors.CAENels_bimorph_mirror_8_channel import (
    CAENelsBimorphMirror8Channel,
)


class CAENelsBimorphMirror12Channel(CAENelsBimorphMirror8Channel):
    channel_9_voltage_target: EpicsSignal = Component(EpicsSignal, "C9:VTRGT")
    channel_10_voltage_target: EpicsSignal = Component(EpicsSignal, "C10:VTRGT")
    channel_11_voltage_target: EpicsSignal = Component(EpicsSignal, "C11:VTRGT")
    channel_12_voltage_target: EpicsSignal = Component(EpicsSignal, "C12:VTRGT")

    channel_9_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C9:VOUT_RBV"
    )
    channel_10_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C10:VOUT_RBV"
    )
    channel_11_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C11:VOUT_RBV"
    )
    channel_12_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C12:VOUT_RBV"
    )

    channel_9_shift: EpicsSignalRO = Component(EpicsSignalRO, "C9:SHIFT")
    channel_10_shift: EpicsSignalRO = Component(EpicsSignalRO, "C10:SHIFT")
    channel_11_shift: EpicsSignalRO = Component(EpicsSignalRO, "C11:SHIFT")
    channel_12_shift: EpicsSignalRO = Component(EpicsSignalRO, "C12:SHIFT")

    channel_9_voltage_out: EpicsSignal = Component(EpicsSignal, "C9:VOUT")
    channel_10_voltage_out: EpicsSignal = Component(EpicsSignal, "C10:VOUT")
    channel_11_voltage_out: EpicsSignal = Component(EpicsSignal, "C11:VOUT")
    channel_12_voltage_out: EpicsSignal = Component(EpicsSignal, "C12:VOUT")

    channel_9_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C9:VOUT_RBV"
    )
    channel_10_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C10:VOUT_RBV"
    )
    channel_11_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C11:VOUT_RBV"
    )
    channel_12_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C12:VOUT_RBV"
    )

    channel_9_status: EpicsSignal = Component(EpicsSignal, "C9:STATUS")
    channel_10_status: EpicsSignal = Component(EpicsSignal, "C10:STATUS")
    channel_11_status: EpicsSignal = Component(EpicsSignal, "C11:STATUS")
    channel_12_status: EpicsSignal = Component(EpicsSignal, "C12:STATUS")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._voltage_target_channels.extend(
            [
                self.channel_9_voltage_target,
                self.channel_10_voltage_target,
                self.channel_11_voltage_target,
                self.channel_12_voltage_target,
            ]
        )

        self._voltage_target_readback_value_channels.extend(
            [
                self.channel_9_voltage_target_readback_value,
                self.channel_10_voltage_target_readback_value,
                self.channel_11_voltage_target_readback_value,
                self.channel_12_voltage_target_readback_value,
            ]
        )

        self._shift_channels.extend(
            [
                self.channel_9_shift,
                self.channel_10_shift,
                self.channel_11_shift,
                self.channel_12_shift,
            ]
        )

        self._voltage_out_channels.extend(
            [
                self.channel_9_voltage_out,
                self.channel_10_voltage_out,
                self.channel_11_voltage_out,
                self.channel_12_voltage_out,
            ]
        )

        self._voltage_out_readback_value_channels.extend(
            [
                self.channel_9_voltage_out_readback_value,
                self.channel_10_voltage_out_readback_value,
                self.channel_11_voltage_out_readback_value,
                self.channel_12_voltage_out_readback_value,
            ]
        )

        self._status_channels.extend(
            [
                self.channel_9_status,
                self.channel_10_status,
                self.channel_11_status,
                self.channel_12_status,
            ]
        )
