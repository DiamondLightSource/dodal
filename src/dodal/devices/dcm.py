from bluesky.protocols import HasHints, Hints
from ophyd_async.core import StandardReadable
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r

from dodal.beamlines.beamline_parameters import get_beamline_parameters


class DCM(StandardReadable, HasHints):
    """
    A double crystal monochromator (DCM), used to select the energy of the beam.

    perp describes the gap between the 2 DCM crystals which has to change as you alter
    the angle to select the requested energy.

    offset ensures that the beam exits the DCM at the same point, regardless of energy.
    """

    def __init__(
        self,
        prefix: str,
        daq_configuration_path: str,
        name: str = "",
    ) -> None:
        self.bragg_in_degrees = Motor(prefix + "-MO-DCM-01:BRAGG")
        self.roll_in_mrad = Motor(prefix + "-MO-DCM-01:ROLL")
        self.offset_in_mm = Motor(prefix + "-MO-DCM-01:OFFSET")
        self.perp_in_mm = Motor(prefix + "-MO-DCM-01:PERP")
        self.energy_in_kev = Motor(prefix + "-MO-DCM-01:ENERGY")
        self.pitch_in_mrad = Motor(prefix + "-MO-DCM-01:PITCH")
        self.wavelength = Motor(prefix + "-MO-DCM-01:WAVELENGTH")

        # temperatures
        self.xtal1_temp = epics_signal_r(float, prefix + "-MO-DCM-01:TEMP1")
        self.xtal2_temp = epics_signal_r(float, prefix + "-MO-DCM-01:TEMP2")
        self.xtal1_heater_temp = epics_signal_r(float, prefix + "-MO-DCM-01:TEMP3")
        self.xtal2_heater_temp = epics_signal_r(float, prefix + "-MO-DCM-01:TEMP4")
        self.backplate_temp = epics_signal_r(float, prefix + "-MO-DCM-01:TEMP5")
        self.perp_temp = epics_signal_r(float, prefix + "-MO-DCM-01:TEMP6")
        self.perp_sub_assembly_temp = epics_signal_r(float, prefix + "-MO-DCM-01:TEMP7")

        self.set_readable_signals(
            read=[
                self.bragg_in_degrees,  # type: ignore
                self.roll_in_mrad,  # type: ignore
                self.offset_in_mm,  # type: ignore
                self.perp_in_mm,  # type: ignore
                self.energy_in_kev,  # type: ignore
                self.pitch_in_mrad,  # type: ignore
                self.wavelength,  # type: ignore
                self.xtal1_temp,
                self.xtal2_temp,
                self.xtal1_heater_temp,
                self.xtal2_heater_temp,
                self.backplate_temp,
                self.perp_temp,
                self.perp_sub_assembly_temp,
            ]
        )

        super().__init__(name)

        # These attributes are just used by hyperion for lookup purposes
        self.dcm_pitch_converter_lookup_table_path = (
            daq_configuration_path + "/lookup/BeamLineEnergy_DCM_Pitch_converter.txt"
        )
        self.dcm_roll_converter_lookup_table_path = (
            daq_configuration_path + "/lookup/BeamLineEnergy_DCM_Roll_converter.txt"
        )
        # I03 configures the DCM Perp as a side effect of applying this fixed value to the DCM Offset after an energy change
        # Nb this parameter is misleadingly named to confuse you
        self.fixed_offset_mm = get_beamline_parameters(
            daq_configuration_path + "/domain/beamlineParameters"
        )["DCM_Perp_Offset_FIXED"]

    @property
    def hints(self) -> Hints:
        return {
            "fields": [
                "dcm_bragg_in_degrees",
                "dcm_roll_in_mrad",
                "dcm_offset_in_mm",
                "dcm_perp_in_mm",
                "dcm_energy_in_kev",
                "dcm_pitch_in_mrad",
                "dcm_wavelength",
            ]
        }
