from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO


class Cryo(Device):
    course = Cpt(EpicsSignal, "-EA-CJET-01:COARSE:CTRL")
    fine = Cpt(EpicsSignal, "-EA-CJET-01:FINE:CTRL")
    temp = Cpt(EpicsSignalRO, "-EA-CSTRM-01:TEMP")
    backpress = Cpt(EpicsSignalRO, "-EA-CSTRM-01:BACKPRESS")
