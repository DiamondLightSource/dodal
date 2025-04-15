from bluesky import plan_stubs as bps
from bluesky.utils import MsgGenerator
from ophyd_async.epics.adcore import ADImageMode

from dodal.common.types import MsgGenerator
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
from dodal.devices.electron_analyser.util import to_kinetic_energy
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
) -> MsgGenerator:
    LOGGER.info(f'Configuring analyser with region "{region.name}"')
    low_energy = to_kinetic_energy(
        region.low_energy, region.energy_mode, excitation_energy
    )
    high_energy = to_kinetic_energy(
        region.high_energy, region.energy_mode, excitation_energy
    )
    # Set detector settings, wait for them all to have completed
    # fmt: off
    yield from bps.mv(
        analyser.low_energy, low_energy,
        analyser.high_energy, high_energy,
        analyser.slices, region.slices,
        analyser.lens_mode, region.lens_mode,
        analyser.pass_energy, region.pass_energy,
        analyser.iterations, region.iterations,
        analyser.acquisition_mode, region.acquisition_mode,
    )
    # fmt: on


def configure_specs(
    analyser: SpecsAnalyserDriverIO, region: SpecsRegion, excitation_energy: float
) -> MsgGenerator:
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
        analyser.adbase_cam.image_mode, ADImageMode.SINGLE,
    )
    # fmt: on
