from ophyd import Component as Cpt
from ophyd import Device, EpicsSignalRO


class ReadOnlyEnergyAndAttenuator(Device):
    transmission = Cpt(EpicsSignalRO, "-OP-ATTN-01:MATCH")
    wavelength = Cpt(EpicsSignalRO, "-MO-DCM-01:LAMBDA")
    energy = Cpt(EpicsSignalRO, "-MO-DCM-01:ENERGY.RBV")
    intensity = Cpt(EpicsSignalRO, "-EA-XBPM-01:SumAll:MeanValue_RBV")
