from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor


class DCM(StandardReadable):
    """
    A double crystal monocromator device, used to select the beam energy.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            # Motors
            self.bragg_in_degrees = Motor(prefix + "-MO-DCM-01:BRAGG")
            self.x_translation_in_mm = Motor(prefix + "-MO-DCM-01:X")
            self.offset_in_mm = Motor(prefix + "-MO-DCM-01:OFFSET")
            self.gap_in_mm = Motor(prefix + "-MO-DCM-01:GAP")
            self.energy_in_kev = Motor(prefix + "-MO-DCM-01:ENERGY")
            self.xtal1_roll = Motor(prefix + "-MO-DCM-01:XTAL1:ROLL")
            self.xtal2_roll = Motor(prefix + "-MO-DCM-01:XTAL2:ROLL")
            self.xtal2_pitch = Motor(prefix + "-MO-DCM-01:XTAL2:PITCH")

            # Wavelength is calculated in epics from the energy
            self.wavelength_in_a = epics_signal_r(float, prefix + "-MO-DCM-01:LAMBDA")

            # Temperatures
            self.xtal1_temp = epics_signal_r(float, prefix + "-DI-DCM-01:PT100-1")
            self.xtal1_heater_temp = epics_signal_r(
                float, prefix + "-DI-DCM-01:PT100-2"
            )
            self.xtal2_temp = epics_signal_r(float, prefix + "-DI-DCM-01:PT100-4")
            self.xtal2_heater_temp = epics_signal_r(
                float, prefix + "-DI-DCM-01:PT100-5"
            )

            self.roll_plate_temp = epics_signal_r(float, prefix + "-DI-DCM-01:PT100-3")
            self.pitch_plate_temp = epics_signal_r(float, prefix + "-DI-DCM-01:PT100-6")
            self.backplate_temp = epics_signal_r(float, prefix + "-DI-DCM-01:PT100-7")
            self.b1_plate_temp = epics_signal_r(float, prefix + "-DI-DCM-01:PT100-7")
            self.gap_temp = epics_signal_r(float, prefix + "-DI-DCM-01:TC-1")

        super().__init__(name)
