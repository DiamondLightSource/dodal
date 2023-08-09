from ophyd import Component as Cpt
from ophyd import Device, EpicsSignalRO


def IPin(Device):
    """Simple device to get the ipin reading"""

    reading: EpicsSignalRO = Cpt(EpicsSignalRO, "I")
