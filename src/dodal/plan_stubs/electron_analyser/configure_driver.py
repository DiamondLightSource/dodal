from bluesky import plan_stubs as bps
from bluesky.utils import MsgGenerator, plan
from ophyd_async.epics.adcore import ADImageMode

from dodal.common.types import MsgGenerator
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
)
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO, SpecsRegion
from dodal.devices.electron_analyser.util import to_kinetic_energy
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaRegion,
)
from dodal.log import LOGGER


@plan
def configure_analyser(
    analyser: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    excitation_energy: float,
) -> MsgGenerator:
    LOGGER.info(f'Configuring analyser with region "{region.name}"')

    low_energy = to_kinetic_energy(
        region.low_energy, region.energy_mode, excitation_energy
    )
    high_energy = to_kinetic_energy(
        region.high_energy, region.energy_mode, excitation_energy
    )
    pass_energy_type = analyser.pass_energy_type
    pass_energy = pass_energy_type(region.pass_energy)

    # Set detector settings, wait for them all to have completed
    # fmt: off
    yield from bps.mv(
        analyser.region_name, region.name,
        analyser.energy_mode, region.energy_mode,
        analyser.excitation_energy, excitation_energy,
        analyser.low_energy, low_energy,
        analyser.high_energy, high_energy,
        analyser.slices, region.slices,
        analyser.lens_mode, region.lens_mode,
        analyser.pass_energy, pass_energy,
        analyser.iterations, region.iterations,
        analyser.acquisition_mode, region.acquisition_mode,
    )
    # fmt: on


@plan
def configure_specs(
    analyser: SpecsAnalyserDriverIO, region: SpecsRegion, excitation_energy: float
) -> MsgGenerator:
    yield from configure_analyser(analyser, region, excitation_energy)
    # fmt: off
    yield from bps.mv(
        analyser.snapshot_values, region.values,
        analyser.psu_mode, region.psu_mode,
    )
    # fmt: on
    if region.acquisition_mode == "Fixed Transmission":
        yield from bps.mv(analyser.centre_energy, region.centre_energy)

    if region.acquisition_mode == "Fixed Energy":
        yield from bps.mv(analyser.energy_step, region.energy_step)


@plan
def configure_vgscienta(
    analyser: VGScientaAnalyserDriverIO, region: VGScientaRegion, excitation_energy
) -> MsgGenerator:
    yield from configure_analyser(analyser, region, excitation_energy)
    centre_energy = to_kinetic_energy(
        region.fix_energy, region.energy_mode, excitation_energy
    )

    # fmt: off
    yield from bps.mv(
        analyser.centre_energy, centre_energy,
        analyser.energy_step, region.energy_step,
        analyser.first_x_channel, region.first_x_channel,
        analyser.first_y_channel, region.first_y_channel,
        analyser.x_channel_size, region.x_channel_size(),
        analyser.y_channel_size, region.y_channel_size(),
        analyser.detector_mode, region.detector_mode,
        analyser.excitation_energy_source, region.excitation_energy_source,
        analyser.image_mode, ADImageMode.SINGLE,
    )
    # fmt: on
