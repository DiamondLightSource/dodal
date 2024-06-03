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
            self.bragg = Motor(prefix + "BRAGG")
            self.crystal_1_roll = Motor(prefix + "XSTAL1:ROLL")
            self.crystal_2_roll = Motor(prefix + "XSTAL2:ROLL")
            self.crystal_1_pitch = Motor(prefix + "XSTAL1:PITCH")
            self.crystal_2_pitch = Motor(prefix + "XSTAL2:PITCH")
            self.offset = Motor(prefix + "OFFSET")
            self.perp = Motor(prefix + "PERP")
            self.energy = Motor(prefix + "ENERGY")
            self.wavelength = Motor(prefix + "WAVELENGTH")

            # temperatures
            self.crystal1_temp = epics_signal_r(float, prefix + "PT100-1")
            self.crystal2_temp = epics_signal_r(float, prefix + "PT100-4")
            self.crystal1_heater_temp = epics_signal_r(float, prefix + "PT100-2")
            self.crystal2_heater_temp = epics_signal_r(float, prefix + "PT100-5")
            self.backplate_temp = epics_signal_r(float, prefix + "PT100-7")
            self.perp_temp = epics_signal_r(float, prefix + "TC-1")

        super().__init__(name)
