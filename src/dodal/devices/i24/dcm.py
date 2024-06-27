from ophyd_async.core import StandardReadable
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r


class DCM(StandardReadable):
    """
    A double crystal monocromator device, used to select the beam energy.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            # Motors
            self.bragg_in_degrees = Motor(prefix + "BRAGG")
            self.x_translation_in_mm = Motor(prefix + "X")
            self.offset_in_mm = Motor(prefix + "OFFSET")
            self.gap_in_mm = Motor(prefix + "GAP")
            self.energy_in_kev = Motor(prefix="ENERGY")
            self.xtal1_roll = Motor(prefix + "XTAL1:ROLL")
            self.xtal2_roll = Motor(prefix + "XTAL2:ROLL")
            self.xtal2_pitch = Motor(prefix + "XTAL2:PITCH")

            # Wavelength is calculated in epics from the energy
            self.wavelength_in_a = epics_signal_r(float, prefix + "LAMBDA")

            # Temperatures
            # NB. temps have different prefix
            self.xtal1_temp = epics_signal_r(float, prefix + "PT100-1")

        super().__init__(name)
