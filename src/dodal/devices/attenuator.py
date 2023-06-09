from ophyd import Component, Device, EpicsSignal


class Attenuator(Device):
    desired_transmission: EpicsSignal = Component(EpicsSignal, ":T2A:SETVAL1")
    use_current_energy: EpicsSignal = Component(
        EpicsSignal, ":E2WL:USECURRENTENERGY.PROC"
    )
    change: EpicsSignal = Component(EpicsSignal, ":FANOUT")
    actual_transmission: EpicsSignal = Component(EpicsSignal, ":MATCH")
