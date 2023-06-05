from ophyd import Component, Device, EpicsSignal, EpicsSignalRO

from dodal.devices.attenuator.attenuator import Attenuator


class AtteunatorFilter(Device):
    pv_calculated_state_0: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.B0")
    pv_calculated_state_1: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.B1")
    pv_calculated_state_2: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.B2")
    pv_calculated_state_3: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.B3")
    pv_calculated_state_4: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.B4")
    pv_calculated_state_5: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.B5")
    pv_calculated_state_6: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.B6")
    pv_calculated_state_7: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.B7")
    pv_calculated_state_8: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.B8")
    pv_calculated_state_9: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.B9")
    pv_calculated_state_10: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.BA")
    pv_calculated_state_11: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.BB")
    pv_calculated_state_12: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.BC")
    pv_calculated_state_13: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.BD")
    pv_calculated_state_14: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.BE")
    pv_calculated_state_15: EpicsSignal = Component(EpicsSignal, ":DEC_TO_BIN.BF")
