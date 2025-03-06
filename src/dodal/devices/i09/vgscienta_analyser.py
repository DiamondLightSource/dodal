from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_w
from sequence import EnergyMode, SESRegion

from dodal.log import LOGGER, do_default_logging_setup

do_default_logging_setup()


class VGScientaAnalyser(StandardReadable):
    """
    Device to configure electron analyser with new region settings.
    """

    PV_LOW_ENERGY = "LOW_ENERGY"
    PV_HIGH_ENERGY = "HIGH_ENERGY"
    PV_CENTRE_ENERGY = "CENTRE_ENERGY"

    PV_SLICES = "SLICES"
    PV_DETECTOR_MODE = "DETECTOR_MODE"
    PV_LENS_MODE = "LENS_MODE"
    PV_PASS_ENERGY = "PASS_ENERGY"
    PV_ENERGY_STEP = "AcquireTime"

    PV_ACQISITION_MODE = "ACQ_MODE"

    ADBASE = "CAM:"
    PV_FIRST_X_CHANNEL = ADBASE + "MinX"
    PV_FIRST_Y_CHANNEL = ADBASE + "MinY"
    PV_LAST_X_CHANNEL = ADBASE + "SizeX"
    PV_LAST_Y_CHANNEL = ADBASE + "SizeY"
    PV_ITERATIONS = ADBASE + "NumExposures"
    PV_IMAGE_MODE = ADBASE + "ImageMode"

    def __init__(self, prefix: str, name: str = "") -> None:
        self.prefix = prefix

        self.name = None
        self.excitation_energy = None
        self.energy_mode = None

        #ToDo
        with self.add_children_as_readables():
            pass

        super(prefix, name)

    def configure_with_region(self, region : SESRegion, excitation_energy_eV : float) -> None:

        LOGGER.info("Configuring electron analyser with region {} and excitation_energy {}eV.", region.name, excitation_energy_eV)

        self.name = region.name
        self.excitation_energy = excitation_energy_eV
        self.energy_mode = region.energyMode

        low_energy = region.lowEnergy if region.energyMode == EnergyMode.KINETIC else excitation_energy_eV - region.highEnergy
        high_energy = region.highEnergy if region.energyMode == EnergyMode.KINETIC else excitation_energy_eV - region.lowEnergy
        centre_energy = region.fixEnergy if region.energyMode == EnergyMode.KINETIC else excitation_energy_eV - region.fixEnergy

        energy_step_eV = region.energyStep / 1000.

        last_x_channel = region.lastXChannel - region.firstXChannel + 1
        last_y_channel = region.lastYChannel - region.firstYChannel + 1

        epics_signal_w(low_energy, self.prefix + VGScientaAnalyser.PV_LOW_ENERGY)
        epics_signal_w(high_energy, self.prefix + VGScientaAnalyser.PV_HIGH_ENERGY)
        epics_signal_w(centre_energy, self.prefix + VGScientaAnalyser.PV_CENTRE_ENERGY)

        epics_signal_w(region.firstXChannel, self.prefix + VGScientaAnalyser.PV_FIRST_X_CHANNEL)
        epics_signal_w(region.firstYChannel, self.prefix + VGScientaAnalyser.PV_FIRST_Y_CHANNEL)
        epics_signal_w(last_x_channel, self.prefix + VGScientaAnalyser.PV_LAST_X_CHANNEL)
        epics_signal_w(last_y_channel, self.prefix + VGScientaAnalyser.PV_LAST_Y_CHANNEL)

        epics_signal_w(region.slices, self.prefix + VGScientaAnalyser.PV_SLICES)
        epics_signal_w(region.detectorMode, self.prefix + VGScientaAnalyser.PV_DETECTOR_MODE)
        epics_signal_w(region.lensMode, self.prefix + VGScientaAnalyser.PV_LENS_MODE)
        epics_signal_w(region.passEnergy, self.prefix + VGScientaAnalyser.PV_PASS_ENERGY)
        epics_signal_w(energy_step_eV, self.prefix + VGScientaAnalyser.PV_ENERGY_STEP)

        epics_signal_w(region.iterations, self.prefix + VGScientaAnalyser.PV_ITERATIONS)
        epics_signal_w(region.iterations, self.prefix + VGScientaAnalyser.PV_IMAGE_MODE)

        epics_signal_w("SINGLE", self.prefix + VGScientaAnalyser.PV_ACQISITION_MODE)

        LOGGER.info("Successfully configured region!")




