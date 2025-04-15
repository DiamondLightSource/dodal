import copy
from collections.abc import Callable, Coroutine
from typing import Any

import bluesky.plan_stubs as bps
from bluesky.utils import plan

from dodal.common.data_util import load_json_file_to_class
from dodal.common.types import MsgGenerator
from dodal.devices.electron_analyser.abstract_analyser import (
    AbstractAnalyserDetector,
)
from dodal.devices.electron_analyser.abstract_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.specs_analyser import SpecsAnalyserDetector
from dodal.devices.electron_analyser.specs_region import SpecsSequence
from dodal.devices.electron_analyser.vgscienta_analyser import (
    VGScientaAnalyserDetector,
)
from dodal.devices.electron_analyser.vgscienta_region import VGScientaSequence
from dodal.log import LOGGER
from dodal.plan_stubs.electron_analyser.configure_controller import (
    configure_specs,
    configure_vgscienta,
)

CONFIGURE_ANALYSER_PLAN = "configure_plan"
SEQUENCE = "sequence"

ANALYSER_TYPE_LOOKUP: dict[
    type[AbstractAnalyserDetector],
    dict[str, type[AbstractBaseSequence] | Callable],
] = {
    VGScientaAnalyserDetector: {
        CONFIGURE_ANALYSER_PLAN: configure_vgscienta,
        SEQUENCE: VGScientaSequence,
    },
    SpecsAnalyserDetector: {
        CONFIGURE_ANALYSER_PLAN: configure_specs,
        SEQUENCE: SpecsSequence,
    },
}


def get_sequence_class_for_analyser(
    analyser: AbstractAnalyserDetector,
) -> type[AbstractBaseSequence[AbstractBaseRegion]]:
    analyser_type = type(analyser)
    sequence_entry = ANALYSER_TYPE_LOOKUP.get(analyser_type)

    if not sequence_entry or SEQUENCE not in sequence_entry:
        raise ValueError(f"No sequence found for analyser type: {analyser_type}")

    sequence = sequence_entry[SEQUENCE]
    if not isinstance(sequence, type):
        raise TypeError("Expected a sequence class type")

    return sequence


def get_configure_plan_for_analyser(
    analyser: AbstractAnalyserDetector,
) -> Callable[..., Coroutine[Any, Any, Any]]:
    analyser_type = type(analyser)
    sequence_entry = ANALYSER_TYPE_LOOKUP.get(analyser_type)

    if not sequence_entry or CONFIGURE_ANALYSER_PLAN not in sequence_entry:
        raise ValueError(f"No configure plan found for analyser type: {analyser_type}")

    configure_plan = sequence_entry[CONFIGURE_ANALYSER_PLAN]
    if not callable(configure_plan):
        raise TypeError("Expected a coroutine-producing callable")

    return configure_plan


@plan
def analyserscan(
    analyser: VGScientaAnalyserDetector | SpecsAnalyserDetector,
    sequence_file: str,
) -> MsgGenerator:
    # ToDo - Add motor arguments to loop through and measure at

    sequence_type = get_sequence_class_for_analyser(analyser)
    sequence = load_json_file_to_class(sequence_type, sequence_file)
    config_plan = get_configure_plan_for_analyser(analyser)

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
