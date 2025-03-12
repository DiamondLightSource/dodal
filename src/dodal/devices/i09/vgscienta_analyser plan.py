from bluesky import plan_stubs as bps

from dodal.devices.i09.ses_region import (
    EnergyMode,
    SESRegion,
)
from dodal.devices.i09.vgscienta_analyser import VGScientaAnalyser
from dodal.log import LOGGER, do_default_logging_setup

do_default_logging_setup()


def configure_detector_with_region(
    detector: VGScientaAnalyser, region: SESRegion, excitation_energy_eV: float
):
    """
    Bluesky plan to setup electron analyser with region.
    """
    LOGGER.info(
        "Configuring electron analyser with region {} and excitation_energy {}eV.",
        region.name,
        excitation_energy_eV,
    )

    # Cache these values as not stored in epics
    detector.region = region
    detector.excitation_energy = excitation_energy_eV
    detector.energy_mode = region.energyMode

    low_energy = (
        region.lowEnergy
        if region.energyMode == EnergyMode.KINETIC
        else excitation_energy_eV - region.highEnergy
    )
    high_energy = (
        region.highEnergy
        if region.energyMode == EnergyMode.KINETIC
        else excitation_energy_eV - region.lowEnergy
    )
    centre_energy = (
        region.fixEnergy
        if region.energyMode == EnergyMode.KINETIC
        else excitation_energy_eV - region.fixEnergy
    )

    energy_step_eV = region.energyStep / 1000.0

    last_x_channel = region.lastXChannel - region.firstXChannel + 1
    last_y_channel = region.lastYChannel - region.firstYChannel + 1

    # Set detector settings, wait for them all to have completed
    # See: https://github.com/bluesky/bluesky/issues/1809
    yield from bps.mv(
        detector.low_energy_signal,  # type: ignore
        low_energy,  # type: ignore
        detector.high_energy_signal,  # type: ignore
        high_energy,  # type: ignore
        detector.centre_energy_signal,  # type: ignore
        centre_energy,  # type: ignore
        detector.first_x_channel_signal,  # type: ignore
        region.firstXChannel,  # type: ignore
        detector.first_y_channel_signal,  # type: ignore
        region.firstYChannel,  # type: ignore
        detector.last_x_channel_signal,  # type: ignore
        last_x_channel,  # type: ignore
        detector.last_y_channel_signal,  # type: ignore
        last_y_channel,  # type: ignore
        detector.slices_signal,  # type: ignore
        region.slices,  # type: ignore
        detector.detector_mode_signal,  # type: ignore
        region.detectorMode,  # type: ignore
        detector.lens_mode_signal,  # type: ignore
        region.lensMode,  # type: ignore
        detector.pass_energy_signal,  # type: ignore
        region.passEnergy,  # type: ignore
        detector.energy_step_signal,  # type: ignore
        energy_step_eV,  # type: ignore
        detector.iterations_signal,  # type: ignore
        region.iterations,  # type: ignore
        detector.image_mode_signal,  # type: ignore
        "SINGLE",  # type: ignore
        detector.acquisition_mode_signal,  # type: ignore
        region.acquisitionMode,  # type: ignore
    )
    LOGGER.info("Successfully configured region!")
