from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor, EpicsSignalRO, Kind


class DCM(Device):
    def __init__(self, *args, daq_configuration_path: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.dcm_pitch_converter_lookup_table_path = (
            daq_configuration_path + "/lookup/BeamLineEnergy_DCM_Pitch_converter.txt"
        )
        self.dcm_roll_converter_lookup_table_path = (
            daq_configuration_path + "/lookup/BeamLineEnergy_DCM_Roll_converter.txt"
        )

    """
    A double crystal monochromator (DCM), used to select the energy of the beam.

    perp describes the gap between the 2 DCM crystals which has to change as you alter
    the angle to select the requested energy.

    offset ensures that the beam exits the DCM at the same point, regardless of energy.
    """

    bragg_in_degrees = Cpt(EpicsMotor, "-MO-DCM-01:BRAGG")
    roll_in_mrad = Cpt(EpicsMotor, "-MO-DCM-01:ROLL")
    offset_in_mm = Cpt(EpicsMotor, "-MO-DCM-01:OFFSET")
    perp_in_mm = Cpt(EpicsMotor, "-MO-DCM-01:PERP")
    energy_in_kev = Cpt(EpicsMotor, "-MO-DCM-01:ENERGY", kind=Kind.hinted)
    pitch_in_mrad = Cpt(EpicsMotor, "-MO-DCM-01:PITCH")
    wavelength = Cpt(EpicsMotor, "-MO-DCM-01:WAVELENGTH")

    # temperatures
    xtal1_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP1")
    xtal2_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP2")
    xtal1_heater_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP3")
    xtal2_heater_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP4")
    backplate_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP5")
    perp_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP6")
    perp_sub_assembly_temp = Cpt(EpicsSignalRO, "-MO-DCM-01:TEMP7")


def fixed_offset_from_beamline_params(gda_beamline_parameters):
    """I03 configures the DCM Perp as a side effect of applying this fixed value to the DCM Offset after an energy change"""
    # Nb this parameter is misleadingly named to confuse you
    return gda_beamline_parameters["DCM_Perp_Offset_FIXED"]
