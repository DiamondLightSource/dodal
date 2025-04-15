from bluesky import plan_stubs as bps

from dodal.devices.electron_analyser.abstract_analyser_io import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract_region import (
    AbstractBaseRegion,
)
from dodal.devices.electron_analyser.specs_analyser_io import (
    SpecsAnalyserDriverIO,
)
from dodal.devices.electron_analyser.specs_region import SpecsRegion
from dodal.devices.electron_analyser.vgscienta_analyser_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta_region import (
    VGScientaRegion,
)
from dodal.log import LOGGER


def configure_analyser(
    analyser: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    excitation_energy: float,
):
    LOGGER.info(f'Configuring analyser with region "{region.name}"')
    low_energy = region.to_kinetic_energy(region.low_energy, excitation_energy)
    high_energy = region.to_kinetic_energy(region.high_energy, excitation_energy)
    pass_energy_type = analyser.pass_energy_type
    pass_energy = pass_energy_type(region.pass_energy)
    # Set detector settings, wait for them all to have completed
    # fmt: off
    yield from bps.mv(
        analyser.low_energy, low_energy,
        analyser.high_energy, high_energy,
        analyser.slices, region.slices,
        analyser.lens_mode, region.lens_mode,
        analyser.pass_energy, pass_energy,
        analyser.iterations, region.iterations,
        analyser.acquisition_mode, region.acquisition_mode,
    )
    # fmt: on


def configure_specs(
    analyser: SpecsAnalyserDriverIO, region: SpecsRegion, excitation_energy: float
):
    yield from configure_analyser(analyser, region, excitation_energy)
    # fmt: off
    yield from bps.mv(
        analyser.values, region.values,
        analyser.psu_mode, region.psu_mode,
    )
    # fmt: on
    if region.acquisition_mode == "Fixed Transmission":
        yield from bps.mv(analyser.centre_energy, region.centre_energy)

    if region.acquisition_mode == "Fixed Energy":
        yield from bps.mv(analyser.energy_step, region.energy_step)


def configure_vgscienta(
    analyser: VGScientaAnalyserDriverIO, region: VGScientaRegion, excitation_energy
):
    yield from configure_analyser(analyser, region, excitation_energy)
    centre_energy = region.to_kinetic_energy(region.fix_energy, excitation_energy)

    # fmt: off
    yield from bps.mv(
        analyser.centre_energy, centre_energy,
        analyser.energy_step, region.energy_step,
        analyser.first_x_channel, region.first_x_channel,
        analyser.first_y_channel, region.first_y_channel,
        analyser.x_channel_size, region.x_channel_size(),
        analyser.y_channel_size, region.y_channel_size(),
        analyser.detector_mode, region.detector_mode,
        analyser.image_mode, "Single",
    )
    # fmt: on
