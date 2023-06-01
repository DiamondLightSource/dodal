from ophyd import Component, Device, EpicsSignal


class Attenuator(Device):
    pv_desired_transmission: EpicsSignal = Component(EpicsSignal, ":T2A:SETVAL1")
    pv_use_current_energy: EpicsSignal = Component(
        EpicsSignal, ":E2WL:USECURRENTENERGY.PROC"
    )
    pv_change: EpicsSignal = Component(EpicsSignal, ":FANOUT")
    pv_actual_transmission: EpicsSignal = Component(EpicsSignal, ":MATCH")


my_att = Attenuator("BL04I-EA-ATTN-01", name="test_attenuator")
my_att.wait_for_connection()
