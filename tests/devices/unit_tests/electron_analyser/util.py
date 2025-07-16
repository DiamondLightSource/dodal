import os
from typing import Any, TypeVar, get_args, get_origin

from ophyd_async.core import SignalR, init_devices

from dodal.devices.electron_analyser import (
    EnergyMode,
)
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    AbstractBaseSequence,
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

TEST_DATA_PATH = "tests/test_data/electron_analyser/"

TEST_VGSCIENTA_SEQUENCE = os.path.join(TEST_DATA_PATH, "vgscienta_sequence.seq")
TEST_SPECS_SEQUENCE = os.path.join(TEST_DATA_PATH, "specs_sequence.seq")

SEQUENCE_KEY = 0
SEQUENCE_TYPE_KEY = 1

TEST_SEQUENCES = {
    VGScientaDetector: [TEST_VGSCIENTA_SEQUENCE, VGScientaSequence],
    VGScientaAnalyserDriverIO: [TEST_VGSCIENTA_SEQUENCE, VGScientaSequence],
    SpecsDetector: [TEST_SPECS_SEQUENCE, SpecsSequence],
    SpecsAnalyserDriverIO: [TEST_SPECS_SEQUENCE, SpecsSequence],
}


def get_test_sequence(key: type) -> str:
    return TEST_SEQUENCES[key][SEQUENCE_KEY]


def get_test_sequence_type(key: type) -> type[AbstractBaseSequence]:
    return TEST_SEQUENCES[key][SEQUENCE_TYPE_KEY]


TEST_SEQUENCE_REGION_NAMES = ["New_Region", "New_Region1"]

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


def assert_region_kinetic_and_binding_energy(r: AbstractBaseRegion) -> None:
    is_binding_energy = r.energy_mode == EnergyMode.BINDING
    is_kinetic_energy = r.energy_mode == EnergyMode.KINETIC
    assert r.is_binding_energy() == is_binding_energy
    assert r.is_binding_energy() != is_kinetic_energy
    assert r.is_kinetic_energy() == is_kinetic_energy
    assert r.is_kinetic_energy() != is_binding_energy


def assert_region_has_expected_values(
    r: AbstractBaseRegion, expected_region_values: dict[str, Any]
) -> None:
    for key in r.__dict__:
        if key in expected_region_values:
            assert r.__dict__[key] == expected_region_values[key]
        else:
            raise KeyError('key "' + key + '" is not in the expected values.')

    for key in expected_region_values.keys():
        assert r.__dict__.get(key) is not None
