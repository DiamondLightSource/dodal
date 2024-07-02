from ophyd import Component, EpicsSignal, EpicsSignalRO

from dodal.devices.bimorph_mirrors.CAENels_bimorph_mirror_16_channel import (
    CAENelsBimorphMirror16Channel,
)


class CAENelsBimorphMirror32Channel(CAENelsBimorphMirror16Channel):
    channel_17_voltage_target: EpicsSignal = Component(EpicsSignal, "C17:VTRGT")
    channel_18_voltage_target: EpicsSignal = Component(EpicsSignal, "C18:VTRGT")
    channel_19_voltage_target: EpicsSignal = Component(EpicsSignal, "C19:VTRGT")
    channel_20_voltage_target: EpicsSignal = Component(EpicsSignal, "C20:VTRGT")
    channel_21_voltage_target: EpicsSignal = Component(EpicsSignal, "C21:VTRGT")
    channel_22_voltage_target: EpicsSignal = Component(EpicsSignal, "C22:VTRGT")
    channel_23_voltage_target: EpicsSignal = Component(EpicsSignal, "C23:VTRGT")
    channel_24_voltage_target: EpicsSignal = Component(EpicsSignal, "C24:VTRGT")
    channel_25_voltage_target: EpicsSignal = Component(EpicsSignal, "C25:VTRGT")
    channel_26_voltage_target: EpicsSignal = Component(EpicsSignal, "C26:VTRGT")
    channel_27_voltage_target: EpicsSignal = Component(EpicsSignal, "C27:VTRGT")
    channel_28_voltage_target: EpicsSignal = Component(EpicsSignal, "C28:VTRGT")
    channel_29_voltage_target: EpicsSignal = Component(EpicsSignal, "C29:VTRGT")
    channel_30_voltage_target: EpicsSignal = Component(EpicsSignal, "C30:VTRGT")
    channel_31_voltage_target: EpicsSignal = Component(EpicsSignal, "C31:VTRGT")
    channel_32_voltage_target: EpicsSignal = Component(EpicsSignal, "C32:VTRGT")

    channel_17_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C17:VOUT_RBV"
    )
    channel_18_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C18:VOUT_RBV"
    )
    channel_19_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C19:VOUT_RBV"
    )
    channel_20_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C20:VOUT_RBV"
    )
    channel_21_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C21:VOUT_RBV"
    )
    channel_22_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C22:VOUT_RBV"
    )
    channel_23_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C23:VOUT_RBV"
    )
    channel_24_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C24:VOUT_RBV"
    )
    channel_25_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C25:VOUT_RBV"
    )
    channel_26_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C26:VOUT_RBV"
    )
    channel_27_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C27:VOUT_RBV"
    )
    channel_28_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C28:VOUT_RBV"
    )
    channel_29_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C29:VOUT_RBV"
    )
    channel_30_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C30:VOUT_RBV"
    )
    channel_31_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C31:VOUT_RBV"
    )
    channel_32_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C32:VOUT_RBV"
    )

    channel_17_shift: EpicsSignalRO = Component(EpicsSignalRO, "C17:SHIFT")
    channel_18_shift: EpicsSignalRO = Component(EpicsSignalRO, "C18:SHIFT")
    channel_19_shift: EpicsSignalRO = Component(EpicsSignalRO, "C19:SHIFT")
    channel_20_shift: EpicsSignalRO = Component(EpicsSignalRO, "C20:SHIFT")
    channel_21_shift: EpicsSignalRO = Component(EpicsSignalRO, "C21:SHIFT")
    channel_22_shift: EpicsSignalRO = Component(EpicsSignalRO, "C22:SHIFT")
    channel_23_shift: EpicsSignalRO = Component(EpicsSignalRO, "C23:SHIFT")
    channel_24_shift: EpicsSignalRO = Component(EpicsSignalRO, "C24:SHIFT")
    channel_25_shift: EpicsSignalRO = Component(EpicsSignalRO, "C25:SHIFT")
    channel_26_shift: EpicsSignalRO = Component(EpicsSignalRO, "C26:SHIFT")
    channel_27_shift: EpicsSignalRO = Component(EpicsSignalRO, "C27:SHIFT")
    channel_28_shift: EpicsSignalRO = Component(EpicsSignalRO, "C28:SHIFT")
    channel_29_shift: EpicsSignalRO = Component(EpicsSignalRO, "C29:SHIFT")
    channel_30_shift: EpicsSignalRO = Component(EpicsSignalRO, "C30:SHIFT")
    channel_31_shift: EpicsSignalRO = Component(EpicsSignalRO, "C31:SHIFT")
    channel_32_shift: EpicsSignalRO = Component(EpicsSignalRO, "C32:SHIFT")

    channel_17_voltage_out: EpicsSignal = Component(EpicsSignal, "C17:VOUT")
    channel_18_voltage_out: EpicsSignal = Component(EpicsSignal, "C18:VOUT")
    channel_19_voltage_out: EpicsSignal = Component(EpicsSignal, "C19:VOUT")
    channel_20_voltage_out: EpicsSignal = Component(EpicsSignal, "C20:VOUT")
    channel_21_voltage_out: EpicsSignal = Component(EpicsSignal, "C21:VOUT")
    channel_22_voltage_out: EpicsSignal = Component(EpicsSignal, "C22:VOUT")
    channel_23_voltage_out: EpicsSignal = Component(EpicsSignal, "C23:VOUT")
    channel_24_voltage_out: EpicsSignal = Component(EpicsSignal, "C24:VOUT")
    channel_25_voltage_out: EpicsSignal = Component(EpicsSignal, "C25:VOUT")
    channel_26_voltage_out: EpicsSignal = Component(EpicsSignal, "C26:VOUT")
    channel_27_voltage_out: EpicsSignal = Component(EpicsSignal, "C27:VOUT")
    channel_28_voltage_out: EpicsSignal = Component(EpicsSignal, "C28:VOUT")
    channel_29_voltage_out: EpicsSignal = Component(EpicsSignal, "C29:VOUT")
    channel_30_voltage_out: EpicsSignal = Component(EpicsSignal, "C30:VOUT")
    channel_31_voltage_out: EpicsSignal = Component(EpicsSignal, "C31:VOUT")
    channel_32_voltage_out: EpicsSignal = Component(EpicsSignal, "C32:VOUT")

    channel_17_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C17:VOUT_RBV"
    )
    channel_18_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C18:VOUT_RBV"
    )
    channel_19_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C19:VOUT_RBV"
    )
    channel_20_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C20:VOUT_RBV"
    )
    channel_21_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C21:VOUT_RBV"
    )
    channel_22_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C22:VOUT_RBV"
    )
    channel_23_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C23:VOUT_RBV"
    )
    channel_24_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C24:VOUT_RBV"
    )
    channel_25_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C25:VOUT_RBV"
    )
    channel_26_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C26:VOUT_RBV"
    )
    channel_27_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C27:VOUT_RBV"
    )
    channel_28_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C28:VOUT_RBV"
    )
    channel_29_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C29:VOUT_RBV"
    )
    channel_30_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C30:VOUT_RBV"
    )
    channel_31_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C31:VOUT_RBV"
    )
    channel_32_voltage_out_readback_value: EpicsSignal = Component(
        EpicsSignal, "C32:VOUT_RBV"
    )

    channel_17_status: EpicsSignal = Component(EpicsSignal, "C17:STATUS")
    channel_18_status: EpicsSignal = Component(EpicsSignal, "C18:STATUS")
    channel_19_status: EpicsSignal = Component(EpicsSignal, "C19:STATUS")
    channel_20_status: EpicsSignal = Component(EpicsSignal, "C20:STATUS")
    channel_21_status: EpicsSignal = Component(EpicsSignal, "C21:STATUS")
    channel_22_status: EpicsSignal = Component(EpicsSignal, "C22:STATUS")
    channel_23_status: EpicsSignal = Component(EpicsSignal, "C23:STATUS")
    channel_24_status: EpicsSignal = Component(EpicsSignal, "C24:STATUS")
    channel_25_status: EpicsSignal = Component(EpicsSignal, "C25:STATUS")
    channel_26_status: EpicsSignal = Component(EpicsSignal, "C26:STATUS")
    channel_27_status: EpicsSignal = Component(EpicsSignal, "C27:STATUS")
    channel_28_status: EpicsSignal = Component(EpicsSignal, "C28:STATUS")
    channel_29_status: EpicsSignal = Component(EpicsSignal, "C29:STATUS")
    channel_30_status: EpicsSignal = Component(EpicsSignal, "C30:STATUS")
    channel_31_status: EpicsSignal = Component(EpicsSignal, "C31:STATUS")
    channel_32_status: EpicsSignal = Component(EpicsSignal, "C32:STATUS")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._voltage_target_channels.extend(
            [
                self.channel_17_voltage_target,
                self.channel_18_voltage_target,
                self.channel_19_voltage_target,
                self.channel_20_voltage_target,
                self.channel_21_voltage_target,
                self.channel_22_voltage_target,
                self.channel_23_voltage_target,
                self.channel_24_voltage_target,
                self.channel_25_voltage_target,
                self.channel_26_voltage_target,
                self.channel_27_voltage_target,
                self.channel_28_voltage_target,
                self.channel_29_voltage_target,
                self.channel_30_voltage_target,
                self.channel_31_voltage_target,
                self.channel_32_voltage_target,
            ]
        )

        self._voltage_target_readback_value_channels.extend(
            [
                self.channel_17_voltage_target_readback_value,
                self.channel_18_voltage_target_readback_value,
                self.channel_19_voltage_target_readback_value,
                self.channel_20_voltage_target_readback_value,
                self.channel_21_voltage_target_readback_value,
                self.channel_22_voltage_target_readback_value,
                self.channel_23_voltage_target_readback_value,
                self.channel_24_voltage_target_readback_value,
                self.channel_25_voltage_target_readback_value,
                self.channel_26_voltage_target_readback_value,
                self.channel_27_voltage_target_readback_value,
                self.channel_28_voltage_target_readback_value,
                self.channel_29_voltage_target_readback_value,
                self.channel_30_voltage_target_readback_value,
                self.channel_31_voltage_target_readback_value,
                self.channel_32_voltage_target_readback_value,
            ]
        )

        self._shift_channels.extend(
            [
                self.channel_17_shift,
                self.channel_18_shift,
                self.channel_19_shift,
                self.channel_20_shift,
                self.channel_21_shift,
                self.channel_22_shift,
                self.channel_23_shift,
                self.channel_24_shift,
                self.channel_25_shift,
                self.channel_26_shift,
                self.channel_27_shift,
                self.channel_28_shift,
                self.channel_29_shift,
                self.channel_30_shift,
                self.channel_31_shift,
                self.channel_32_shift,
            ]
        )

        self._voltage_out_channels.extend(
            [
                self.channel_17_voltage_out,
                self.channel_18_voltage_out,
                self.channel_19_voltage_out,
                self.channel_20_voltage_out,
                self.channel_21_voltage_out,
                self.channel_22_voltage_out,
                self.channel_23_voltage_out,
                self.channel_24_voltage_out,
                self.channel_25_voltage_out,
                self.channel_26_voltage_out,
                self.channel_27_voltage_out,
                self.channel_28_voltage_out,
                self.channel_29_voltage_out,
                self.channel_30_voltage_out,
                self.channel_31_voltage_out,
                self.channel_32_voltage_out,
            ]
        )

        self._voltage_out_readback_value_channels.extend(
            [
                self.channel_17_voltage_out_readback_value,
                self.channel_18_voltage_out_readback_value,
                self.channel_19_voltage_out_readback_value,
                self.channel_20_voltage_out_readback_value,
                self.channel_21_voltage_out_readback_value,
                self.channel_22_voltage_out_readback_value,
                self.channel_23_voltage_out_readback_value,
                self.channel_24_voltage_out_readback_value,
                self.channel_25_voltage_out_readback_value,
                self.channel_26_voltage_out_readback_value,
                self.channel_27_voltage_out_readback_value,
                self.channel_28_voltage_out_readback_value,
                self.channel_29_voltage_out_readback_value,
                self.channel_30_voltage_out_readback_value,
                self.channel_31_voltage_out_readback_value,
                self.channel_32_voltage_out_readback_value,
            ]
        )

        self._status_channels.extend(
            [
                self.channel_17_status,
                self.channel_18_status,
                self.channel_19_status,
                self.channel_20_status,
                self.channel_21_status,
                self.channel_22_status,
                self.channel_23_status,
                self.channel_24_status,
                self.channel_25_status,
                self.channel_26_status,
                self.channel_27_status,
                self.channel_28_status,
                self.channel_29_status,
                self.channel_30_status,
                self.channel_31_status,
                self.channel_32_status,
            ]
        )
