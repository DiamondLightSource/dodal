from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_w
from sequence import EnergyMode, SESRegion

from dodal.log import LOGGER, do_default_logging_setup

do_default_logging_setup()


class VGScientaAnalyser(StandardReadable):
    """
    Device to configure electron analyser with new region settings.
    """

    LOW_ENERGY = "LOW_ENERGY"
    HIGH_ENERGY = "HIGH_ENERGY"
    CENTRE_ENERGY = "CENTRE_ENERGY"

    SLICES = "SLICES"
    DETECTOR_MODE = "DETECTOR_MODE"
    LENS_MODE = "LENS_MODE"
    PASS_ENERGY = "PASS_ENERGY"
    ENERGY_STEP = "AcquireTime"

    ACQISITION_MODE = "ACQ_MODE"

    ADBASE = "CAM:"
    FIRST_X_CHANNEL = ADBASE + "MinX"
    FIRST_Y_CHANNEL = ADBASE + "MinY"
    LAST_X_CHANNEL = ADBASE + "SizeX"
    LAST_Y_CHANNEL = ADBASE + "SizeY"
    ITERATIONS = ADBASE + "NumExposures"
    IMAGE_MODE = ADBASE + "ImageMode"

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

        epics_signal_w(low_energy, self.prefix + VGScientaAnalyser.LOW_ENERGY)
        epics_signal_w(high_energy, self.prefix + VGScientaAnalyser.HIGH_ENERGY)
        epics_signal_w(centre_energy, self.prefix + VGScientaAnalyser.CENTRE_ENERGY)

        epics_signal_w(region.firstXChannel, self.prefix + VGScientaAnalyser.FIRST_X_CHANNEL)
        epics_signal_w(region.firstYChannel, self.prefix + VGScientaAnalyser.FIRST_Y_CHANNEL)
        epics_signal_w(last_x_channel, self.prefix + VGScientaAnalyser.LAST_X_CHANNEL)
        epics_signal_w(last_y_channel, self.prefix + VGScientaAnalyser.LAST_Y_CHANNEL)

        epics_signal_w(region.slices, self.prefix + VGScientaAnalyser.SLICES)
        epics_signal_w(region.detectorMode, self.prefix + VGScientaAnalyser.DETECTOR_MODE)
        epics_signal_w(region.lensMode, self.prefix + VGScientaAnalyser.LENS_MODE)
        epics_signal_w(region.passEnergy, self.prefix + VGScientaAnalyser.PASS_ENERGY)
        epics_signal_w(energy_step_eV, self.prefix + VGScientaAnalyser.ENERGY_STEP)

        epics_signal_w(region.iterations, self.prefix + VGScientaAnalyser.ITERATIONS)
        epics_signal_w(region.iterations, self.prefix + VGScientaAnalyser.IMAGE_MODE)

        epics_signal_w("SINGLE", self.prefix + VGScientaAnalyser.ACQISITION_MODE)

        LOGGER.info("Successfully configured region!")




