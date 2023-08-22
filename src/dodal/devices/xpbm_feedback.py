from ophyd import Component as Cpt
from ophyd import Device, EpicsSignalRO


class XBPMFeedback(Device):
    pos_ok: EpicsSignalRO = Cpt(EpicsSignalRO, "-EA-FDBK-01:XBPM2POSITION_OK")
    x: EpicsSignalRO = Cpt(EpicsSignalRO, "-EA-XBPM-02:PosX:MeanValue_RBV")
    y: EpicsSignalRO = Cpt(EpicsSignalRO, "-EA-XBPM-02:PosY:MeanValue_RBV")
