from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor, EpicsSignalRO, Kind


class DCM(Device):
    """
    A double crystal monochromator (DCM), used to select the energy of the beam.

    perp describes the gap between the 2 DCM crystals which has to change as you alter
    the angle to select the requested energy.

    offset ensures that the beam exits the DCM at the same point, regardless of energy.
    """

    bragg = Cpt(EpicsMotor, "-MO-DCM-01:BRAGG")
    roll = Cpt(EpicsMotor, "-MO-DCM-01:ROLL")
    offset = Cpt(EpicsMotor, "-MO-DCM-01:OFFSET")
    perp = Cpt(EpicsMotor, "-MO-DCM-01:PERP")
    energy_in_kev = Cpt(EpicsMotor, "-MO-DCM-01:ENERGY", kind=Kind.hinted)
    pitch = Cpt(EpicsMotor, "-MO-DCM-01:PITCH")
    wavelength = Cpt(EpicsMotor, "-MO-DCM-01:WAVELENGTH")

    # temperatures
    xtal1_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP1")
    xtal2_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP2")
    xtal1_heater_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP3")
    xtal2_heater_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP4")
    backplate_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP5")
    perp_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP6")
    perp_sub_assembly_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP7")
