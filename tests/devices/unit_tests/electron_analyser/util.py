from typing import Any, TypeVar, get_args, get_origin

from deepdiff import DeepDiff
from ophyd_async.core import SignalR, init_devices

from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    AbstractElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.specs import (
    SpecsAnalyserDriverIO,
    SpecsDetector,
    SpecsSequence,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaDetector,
    VGScientaSequence,
)
from tests.devices.unit_tests.electron_analyser.test_data import (
    TEST_SPECS_SEQUENCE,
    TEST_VGSCIENTA_SEQUENCE,
)

SEQUENCE_KEY = 0
SEQUENCE_TYPE_KEY = 1

TEST_SEQUENCES = {
    VGScientaSequence: TEST_VGSCIENTA_SEQUENCE,
    VGScientaDetector: TEST_VGSCIENTA_SEQUENCE,
    VGScientaAnalyserDriverIO: TEST_VGSCIENTA_SEQUENCE,
    SpecsSequence: TEST_SPECS_SEQUENCE,
    SpecsDetector: TEST_SPECS_SEQUENCE,
    SpecsAnalyserDriverIO: TEST_SPECS_SEQUENCE,
}


def get_test_sequence(key: type) -> str:
    for cls in key.__mro__:
        # Check for unscripted class only
        if cls in TEST_SEQUENCES:
            return TEST_SEQUENCES[cls]
    raise KeyError(f"Found no match with type {key}")


TEST_SEQUENCE_REGION_NAMES = ["New_Region", "New_Region1", "New_Region2"]

_TDevice = TypeVar(
    "_TDevice", bound=AbstractElectronAnalyserDetector | AbstractAnalyserDriverIO
)


async def create_analyser_device(
    device_class: type[_TDevice],
    energy_sources: dict[str, SignalR[float]],
) -> _TDevice:
    parameters = {
        "prefix": "TEST:",
        "lens_mode_type": get_args(device_class)[0],
        "psu_mode_type": get_args(device_class)[1],
        "energy_sources": energy_sources,
    }
    origin = get_origin(device_class)
    if origin in (VGScientaDetector, VGScientaAnalyserDriverIO):
        parameters["pass_energy_type"] = get_args(device_class)[2]

    is_detector = isinstance(device_class, AbstractElectronAnalyserDetector)
    parameters["name"] = "sim_detector" if is_detector else "sim_driver"

    async with init_devices(mock=True, connect=True):
        device = device_class(**parameters)
    return device


def assert_region_has_expected_values(
    r: AbstractBaseRegion, expected_region_values: dict[str, Any]
) -> None:
    actual_values = r.__dict__
    diff = DeepDiff(expected_region_values, actual_values)
    if diff:
        raise AssertionError(f"Region does not match expected values:\n{diff}")
    for key in expected_region_values.keys():
        assert actual_values.get(key) is not None
