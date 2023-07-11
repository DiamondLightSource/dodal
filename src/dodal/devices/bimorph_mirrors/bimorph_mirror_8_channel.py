from enum import Enum

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO


class BimorphMirror8Channel(Device):
    all_target_proc: EpicsSignal = Component(EpicsSignal, "ALLTRGT.PROC")
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

    channel_1_voltage_target: EpicsSignal = Component(EpicsSignal, "C1:VTRGT")
    channel_2_voltage_target: EpicsSignal = Component(EpicsSignal, "C2:VTRGT")
    channel_3_voltage_target: EpicsSignal = Component(EpicsSignal, "C3:VTRGT")
    channel_4_voltage_target: EpicsSignal = Component(EpicsSignal, "C4:VTRGT")
    channel_5_voltage_target: EpicsSignal = Component(EpicsSignal, "C5:VTRGT")
    channel_6_voltage_target: EpicsSignal = Component(EpicsSignal, "C6:VTRGT")
    channel_7_voltage_target: EpicsSignal = Component(EpicsSignal, "C7:VTRGT")
    channel_8_voltage_target: EpicsSignal = Component(EpicsSignal, "C8:VTRGT")

    channel_1_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C1:VTRGT_RBV"
    )
    channel_2_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C2:VTRGT_RBV"
    )
    channel_3_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C3:VTRGT_RBV"
    )
    channel_4_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C4:VTRGT_RBV"
    )
    channel_5_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C5:VTRGT_RBV"
    )
    channel_6_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C6:VTRGT_RBV"
    )
    channel_7_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C7:VTRGT_RBV"
    )
    channel_8_voltage_target_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C8:VTRGT_RBV"
    )

    channel_1_shift: EpicsSignal = Component(EpicsSignal, "C1:SHIFT")
    channel_2_shift: EpicsSignal = Component(EpicsSignal, "C2:SHIFT")
    channel_3_shift: EpicsSignal = Component(EpicsSignal, "C3:SHIFT")
    channel_4_shift: EpicsSignal = Component(EpicsSignal, "C4:SHIFT")
    channel_5_shift: EpicsSignal = Component(EpicsSignal, "C5:SHIFT")
    channel_6_shift: EpicsSignal = Component(EpicsSignal, "C6:SHIFT")
    channel_7_shift: EpicsSignal = Component(EpicsSignal, "C7:SHIFT")
    channel_8_shift: EpicsSignal = Component(EpicsSignal, "C8:SHIFT")

    channel_1_voltage_out: EpicsSignal = Component(EpicsSignal, "C1:VOUT")
    channel_2_voltage_out: EpicsSignal = Component(EpicsSignal, "C2:VOUT")
    channel_3_voltage_out: EpicsSignal = Component(EpicsSignal, "C3:VOUT")
    channel_4_voltage_out: EpicsSignal = Component(EpicsSignal, "C4:VOUT")
    channel_5_voltage_out: EpicsSignal = Component(EpicsSignal, "C5:VOUT")
    channel_6_voltage_out: EpicsSignal = Component(EpicsSignal, "C6:VOUT")
    channel_7_voltage_out: EpicsSignal = Component(EpicsSignal, "C7:VOUT")
    channel_8_voltage_out: EpicsSignal = Component(EpicsSignal, "C8:VOUT")

    channel_1_voltage_out_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C1:VOUT_RBV"
    )
    channel_2_voltage_out_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C2:VOUT_RBV"
    )
    channel_3_voltage_out_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C3:VOUT_RBV"
    )
    channel_4_voltage_out_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C4:VOUT_RBV"
    )
    channel_5_voltage_out_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C5:VOUT_RBV"
    )
    channel_6_voltage_out_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C6:VOUT_RBV"
    )
    channel_7_voltage_out_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C7:VOUT_RBV"
    )
    channel_8_voltage_out_readback_value: EpicsSignalRO = Component(
        EpicsSignalRO, "C8:VOUT_RBV"
    )

    channel_1_status: EpicsSignalRO = Component(EpicsSignalRO, "C1:STATUS")
    channel_2_status: EpicsSignalRO = Component(EpicsSignalRO, "C2:STATUS")
    channel_3_status: EpicsSignalRO = Component(EpicsSignalRO, "C3:STATUS")
    channel_4_status: EpicsSignalRO = Component(EpicsSignalRO, "C4:STATUS")
    channel_5_status: EpicsSignalRO = Component(EpicsSignalRO, "C5:STATUS")
    channel_6_status: EpicsSignalRO = Component(EpicsSignalRO, "C6:STATUS")
    channel_7_status: EpicsSignalRO = Component(EpicsSignalRO, "C7:STATUS")
    channel_8_status: EpicsSignalRO = Component(EpicsSignalRO, "C8:STATUS")
