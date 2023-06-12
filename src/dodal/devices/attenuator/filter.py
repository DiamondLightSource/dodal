from ophyd import Component, Device, EpicsSignal

from dodal.devices.attenuator.attenuator import Attenuator


class AtteunatorFilter(Device):
    actual_filter_state: EpicsSignal = Component(EpicsSignal, ":INLIM")
