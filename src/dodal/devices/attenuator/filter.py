from ophyd import Component, Device, EpicsSignalRO


class AtteunatorFilter(Device):
    actual_filter_state: EpicsSignalRO = Component(EpicsSignalRO, ":INLIM")
