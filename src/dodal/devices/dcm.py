from ophyd_async.core import StandardReadable
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r


class DCM(StandardReadable):
    """
    A double crystal monochromator (DCM), used to select the energy of the beam.

    perp describes the gap between the 2 DCM crystals which has to change as you alter
    the angle to select the requested energy.

    offset ensures that the beam exits the DCM at the same point, regardless of energy.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.bragg_in_degrees = Motor(prefix + "BRAGG")
            self.roll_in_mrad = Motor(prefix + "ROLL")
            self.offset_in_mm = Motor(prefix + "OFFSET")
            self.perp_in_mm = Motor(prefix + "PERP")
            self.energy_in_kev = Motor(prefix + "ENERGY")
            self.pitch_in_mrad = Motor(prefix + "PITCH")
            self.wavelength = Motor(prefix + "WAVELENGTH")

            # temperatures
            self.xtal1_temp = epics_signal_r(float, prefix + "TEMP1")
            self.xtal2_temp = epics_signal_r(float, prefix + "TEMP2")
            self.xtal1_heater_temp = epics_signal_r(float, prefix + "TEMP3")
            self.xtal2_heater_temp = epics_signal_r(float, prefix + "TEMP4")
            self.backplate_temp = epics_signal_r(float, prefix + "TEMP5")
            self.perp_temp = epics_signal_r(float, prefix + "TEMP6")
            self.perp_sub_assembly_temp = epics_signal_r(float, prefix + "TEMP7")

        super().__init__(name)
