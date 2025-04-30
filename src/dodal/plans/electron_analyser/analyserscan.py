import copy
from collections.abc import Callable, Coroutine
from typing import Any

import bluesky.plan_stubs as bps
from bluesky.utils import plan

from dodal.common.types import MsgGenerator
from dodal.devices.electron_analyser.abstract_analyser import (
    AbstractAnalyserDriverIO,
    AbstractElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.abstract_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.specs_analyser import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.vgscienta_analyser import VGScientaAnalyserDriverIO
from dodal.log import LOGGER
from dodal.plan_stubs.electron_analyser.configure_driver import (
    configure_specs,
    configure_vgscienta,
)

ANALYSER_TYPE_LOOKUP: dict[type[AbstractAnalyserDriverIO], Callable] = {
    VGScientaAnalyserDriverIO: configure_vgscienta,
    SpecsAnalyserDriverIO: configure_specs,
}


def get_configure_plan_for_analyser(
    analyser: AbstractAnalyserDriverIO,
) -> Callable[..., Coroutine[Any, Any, Any]]:
    configure_plan = ANALYSER_TYPE_LOOKUP.get(type(analyser))

    if configure_plan is None:
        raise ValueError(f"No configure plan found for analyser type: {type(analyser)}")
    return configure_plan


@plan
def analyserscan(
    analyser: AbstractElectronAnalyserDetector[
        AbstractAnalyserDriverIO, AbstractBaseSequence[AbstractBaseRegion]
    ],
    sequence_file: str,
) -> MsgGenerator:
    # ToDo - Add motor arguments to loop through and measure at

    sequence = analyser.get_sequence(sequence_file)
    config_plan = get_configure_plan_for_analyser(analyser.driver)

    LOGGER.info("Found regions: " + str(sequence.get_enabled_region_names()))

    yield from bps.open_run()

    enabled_regions = sequence.get_enabled_regions()

    region_to_analyser = {
        region.name: copy.copy(analyser) for region in enabled_regions
    }

    for region in enabled_regions:
        # ToDo - Add live excitation energy and shutter movement. Inside plan or device?
        # Use place holder for now
        exctiation_energy = 1000

        yield from config_plan(analyser.driver, region, exctiation_energy)
        LOGGER.info(f"Acquiring region {region.name}")

        yield from bps.trigger_and_read(
            [region_to_analyser[region.name]], name=region.name
        )
        LOGGER.info("Finished acquiring region.")

    LOGGER.info("Closing run")
    yield from bps.close_run()
    yield from bps.unstage(analyser)
