from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_w
from sequence import AcquisitionMode, DetectorMode, EnergyMode, SESRegion

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

        self.region = None
        self.excitation_energy = 0
        self.energy_mode = EnergyMode.KINETIC

        self.low_energy_signal = epics_signal_w(float, self.prefix + VGScientaAnalyser.PV_LOW_ENERGY)
        self.high_energy_signal = epics_signal_w(float, self.prefix + VGScientaAnalyser.PV_HIGH_ENERGY)
        self.centre_energy_signal = epics_signal_w(float, self.prefix + VGScientaAnalyser.PV_CENTRE_ENERGY)

        self.first_x_channel_signal = epics_signal_w(int, self.prefix + VGScientaAnalyser.PV_FIRST_X_CHANNEL)
        self.first_y_channel_signal = epics_signal_w(int, self.prefix + VGScientaAnalyser.PV_FIRST_Y_CHANNEL)
        self.last_x_channel_signal = epics_signal_w(int, self.prefix + VGScientaAnalyser.PV_LAST_X_CHANNEL)
        self.last_y_channel_signal = epics_signal_w(int, self.prefix + VGScientaAnalyser.PV_LAST_Y_CHANNEL)

        self.slices_signal = epics_signal_w(int, self.prefix + VGScientaAnalyser.PV_SLICES)
        self.detector_mode_signal = epics_signal_w(DetectorMode, self.prefix + VGScientaAnalyser.PV_DETECTOR_MODE)
        self.lens_mode_signal = epics_signal_w(str, self.prefix + VGScientaAnalyser.PV_LENS_MODE)
        self.pass_energy_signal = epics_signal_w(int, self.prefix + VGScientaAnalyser.PV_PASS_ENERGY)
        self.energy_step_signal = epics_signal_w(float, self.prefix + VGScientaAnalyser.PV_ENERGY_STEP)

        self.iterations_signal = epics_signal_w(int, self.prefix + VGScientaAnalyser.PV_ITERATIONS)
        self.image_mode_signal = epics_signal_w(str, self.prefix + VGScientaAnalyser.PV_IMAGE_MODE)

        self.acquisition_mode_signal = epics_signal_w(AcquisitionMode, self.prefix + VGScientaAnalyser.PV_ACQISITION_MODE)

        #ToDo
        with self.add_children_as_readables():
            pass

        super().__init__(name)

    async def configure_with_region(self, region : SESRegion, excitation_energy_eV : float) -> None:

        LOGGER.info("Configuring electron analyser with region {} and excitation_energy {}eV.", region.name, excitation_energy_eV)

        #Cache these values as not stored in epics
        self.region = region
        self.excitation_energy = excitation_energy_eV
        self.energy_mode = region.energyMode

        low_energy = region.lowEnergy if region.energyMode == EnergyMode.KINETIC else excitation_energy_eV - region.highEnergy
        high_energy = region.highEnergy if region.energyMode == EnergyMode.KINETIC else excitation_energy_eV - region.lowEnergy
        centre_energy = region.fixEnergy if region.energyMode == EnergyMode.KINETIC else excitation_energy_eV - region.fixEnergy

        energy_step_eV = region.energyStep / 1000.

        last_x_channel = region.lastXChannel - region.firstXChannel + 1
        last_y_channel = region.lastYChannel - region.firstYChannel + 1

        await self.low_energy_signal.set(low_energy, wait = True)
        await self.high_energy_signal.set(high_energy, wait = True)
        await self.centre_energy_signal.set(centre_energy, wait = True)

        await self.first_x_channel_signal.set(region.firstXChannel, wait = True)
        await self.first_y_channel_signal.set(region.firstYChannel, wait = True)
        await self.last_x_channel_signal.set(last_x_channel, wait = True)
        await self.last_y_channel_signal.set(last_y_channel, wait = True)

        await self.slices_signal.set(region.slices, wait = True)
        await self.detector_mode_signal.set(region.detectorMode, wait = True)
        await self.lens_mode_signal.set(region.lensMode, wait = True)
        await self.pass_energy_signal.set(region.passEnergy, wait = True)
        await self.energy_step_signal.set(energy_step_eV, wait = True)

        await self.iterations_signal.set(region.iterations, wait = True)
        await self.image_mode_signal.set("SINGLE", wait = True)

        await self.acquisition_mode_signal.set(region.acquisitionMode, wait = True)

        LOGGER.info("Successfully configured region!")
