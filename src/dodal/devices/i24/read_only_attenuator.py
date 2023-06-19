from ophyd import Component as Cpt
from ophyd import Device, EpicsSignalRO


class ReadOnlyEnergyAndAttenuator(Device):
    transmission: EpicsSignalRO = Cpt(EpicsSignalRO, "-OP-ATTN-01:MATCH")
    wavelength: EpicsSignalRO = Cpt(EpicsSignalRO, "-MO-DCM-01:LAMBDA")
    energy: EpicsSignalRO = Cpt(EpicsSignalRO, "-MO-DCM-01:ENERGY.RBV")
    intensity: EpicsSignalRO = Cpt(EpicsSignalRO, "-EA-XBPM-01:SumAll:MeanValue_RBV")
