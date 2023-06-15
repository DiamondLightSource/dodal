from ophyd import Component as Cpt
from ophyd import Device, EpicsSignalRO


class ReadOnlyEnergyAndAttenuator(Device):
    transmission: EpicsSignalRO = Cpt(EpicsSignalRO, "BL24I-OP-ATTN-01:T2A:SETVAL1")
    wavelength: EpicsSignalRO = Cpt(EpicsSignalRO, "BL24I-MO-DCM-01:LAMBDA")
    energy: EpicsSignalRO = Cpt(EpicsSignalRO, "BL24I-MO-DCM-01:ENERGY.RBV")
    intensity: EpicsSignalRO = Cpt(
        EpicsSignalRO, "BL24I-EA-XBPM-01:SumAll:MeanValue_RBV"
    )
