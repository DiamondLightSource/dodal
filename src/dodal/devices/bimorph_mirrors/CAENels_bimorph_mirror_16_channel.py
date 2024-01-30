from ophyd import Component, EpicsSignal, EpicsSignalRO

from dodal.devices.bimorph_mirrors.CAENels_bimorph_mirror_8_channel import (
    CAENelsBimorphMirror8Channel,
)


class CAENelsBimorphMirror16Channel(CAENelsBimorphMirror8Channel):
    channel_9_voltage_target: EpicsSignal = Component(EpicsSignal, "C9:VTRGT")
    channel_10_voltage_target: EpicsSignal = Component(EpicsSignal, "C10:VTRGT")
    channel_11_voltage_target: EpicsSignal = Component(EpicsSignal, "C11:VTRGT")
    channel_12_voltage_target: EpicsSignal = Component(EpicsSignal, "C12:VTRGT")
    channel_13_voltage_target: EpicsSignal = Component(EpicsSignal, "C13:VTRGT")
    channel_14_voltage_target: EpicsSignal = Component(EpicsSignal, "C14:VTRGT")
    channel_15_voltage_target: EpicsSignal = Component(EpicsSignal, "C15:VTRGT")
    channel_16_voltage_target: EpicsSignal = Component(EpicsSignal, "C16:VTRGT")

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
    channel_13_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C13:VOUT_RBV"
    )
    channel_14_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C14:VOUT_RBV"
    )
    channel_15_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C15:VOUT_RBV"
    )
    channel_16_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C16:VOUT_RBV"
    )

    channel_9_shift: EpicsSignalRO = Component(EpicsSignalRO, "C9:SHIFT")
    channel_10_shift: EpicsSignalRO = Component(EpicsSignalRO, "C10:SHIFT")
    channel_11_shift: EpicsSignalRO = Component(EpicsSignalRO, "C11:SHIFT")
    channel_12_shift: EpicsSignalRO = Component(EpicsSignalRO, "C12:SHIFT")
    channel_13_shift: EpicsSignalRO = Component(EpicsSignalRO, "C13:SHIFT")
    channel_14_shift: EpicsSignalRO = Component(EpicsSignalRO, "C14:SHIFT")
    channel_15_shift: EpicsSignalRO = Component(EpicsSignalRO, "C15:SHIFT")
    channel_16_shift: EpicsSignalRO = Component(EpicsSignalRO, "C16:SHIFT")

    channel_9_voltage_out: EpicsSignal = Component(EpicsSignal, "C9:VOUT")
    channel_10_voltage_out: EpicsSignal = Component(EpicsSignal, "C10:VOUT")
    channel_11_voltage_out: EpicsSignal = Component(EpicsSignal, "C11:VOUT")
    channel_12_voltage_out: EpicsSignal = Component(EpicsSignal, "C12:VOUT")
    channel_13_voltage_out: EpicsSignal = Component(EpicsSignal, "C13:VOUT")
    channel_14_voltage_out: EpicsSignal = Component(EpicsSignal, "C14:VOUT")
    channel_15_voltage_out: EpicsSignal = Component(EpicsSignal, "C15:VOUT")
    channel_16_voltage_out: EpicsSignal = Component(EpicsSignal, "C16:VOUT")

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
    channel_13_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C13:VOUT_RBV"
    )
    channel_14_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C14:VOUT_RBV"
    )
    channel_15_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C15:VOUT_RBV"
    )
    channel_16_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C16:VOUT_RBV"
    )

    channel_9_status: EpicsSignal = Component(EpicsSignal, "C9:STATUS")
    channel_10_status: EpicsSignal = Component(EpicsSignal, "C10:STATUS")
    channel_11_status: EpicsSignal = Component(EpicsSignal, "C11:STATUS")
    channel_12_status: EpicsSignal = Component(EpicsSignal, "C12:STATUS")
    channel_13_status: EpicsSignal = Component(EpicsSignal, "C13:STATUS")
    channel_14_status: EpicsSignal = Component(EpicsSignal, "C14:STATUS")
    channel_15_status: EpicsSignal = Component(EpicsSignal, "C15:STATUS")
    channel_16_status: EpicsSignal = Component(EpicsSignal, "C16:STATUS")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._voltage_target_channels.extend(
            [
                self.channel_9_voltage_target,
                self.channel_10_voltage_target,
                self.channel_11_voltage_target,
                self.channel_12_voltage_target,
                self.channel_13_voltage_target,
                self.channel_14_voltage_target,
                self.channel_15_voltage_target,
                self.channel_16_voltage_target,
            ]
        )

        self._voltage_target_readback_value_channels.extend(
            [
                self.channel_9_voltage_target_readback_value,
                self.channel_10_voltage_target_readback_value,
                self.channel_11_voltage_target_readback_value,
                self.channel_12_voltage_target_readback_value,
                self.channel_13_voltage_target_readback_value,
                self.channel_14_voltage_target_readback_value,
                self.channel_15_voltage_target_readback_value,
                self.channel_16_voltage_target_readback_value,
            ]
        )

        self._shift_channels.extend(
            [
                self.channel_9_shift,
                self.channel_10_shift,
                self.channel_11_shift,
                self.channel_12_shift,
                self.channel_13_shift,
                self.channel_14_shift,
                self.channel_15_shift,
                self.channel_16_shift,
            ]
        )

        self._voltage_out_channels.extend(
            [
                self.channel_9_voltage_out,
                self.channel_10_voltage_out,
                self.channel_11_voltage_out,
                self.channel_12_voltage_out,
                self.channel_13_voltage_out,
                self.channel_14_voltage_out,
                self.channel_15_voltage_out,
                self.channel_16_voltage_out,
            ]
        )

        self._voltage_out_readback_value_channels.extend(
            [
                self.channel_9_voltage_out_readback_value,
                self.channel_10_voltage_out_readback_value,
                self.channel_11_voltage_out_readback_value,
                self.channel_12_voltage_out_readback_value,
                self.channel_13_voltage_out_readback_value,
                self.channel_14_voltage_out_readback_value,
                self.channel_15_voltage_out_readback_value,
                self.channel_16_voltage_out_readback_value,
            ]
        )

        self._status_channels.extend(
            [
                self.channel_9_status,
                self.channel_10_status,
                self.channel_11_status,
                self.channel_12_status,
                self.channel_13_status,
                self.channel_14_status,
                self.channel_15_status,
                self.channel_16_status,
            ]
        )
