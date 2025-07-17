import os
from typing import Any

from ophyd_async.core import StandardReadable

from dodal.devices.electron_analyser import EnergyMode
from dodal.devices.electron_analyser.abstract import (
    AbstractBaseRegion,
    AbstractBaseSequence,
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

TEST_LEGACY_VGSCIENTA_SEQUENCE = os.path.join(
    TEST_DATA_PATH, "vgscienta_legacy_sequence.seq"
)
TEST_NEW_SCIENTA_SEQUENCE = os.path.join(TEST_DATA_PATH, "vgscienta_new_sequence.seq")
TEST_LEGACY_SPECS_SEQUENCE = os.path.join(TEST_DATA_PATH, "specs_legacy_sequence.seq")
TEST_NEW_SPECS_SEQUENCE = os.path.join(TEST_DATA_PATH, "specs_new_sequence.seq")

SEQUENCE_KEY = 0
SEQUENCE_TYPE_KEY = 1

TEST_SEQUENCES = {
    VGScientaDetector: [TEST_LEGACY_VGSCIENTA_SEQUENCE, VGScientaSequence],
    VGScientaAnalyserDriverIO: [TEST_LEGACY_VGSCIENTA_SEQUENCE, VGScientaSequence],
    SpecsDetector: [TEST_LEGACY_SPECS_SEQUENCE, SpecsSequence],
    SpecsAnalyserDriverIO: [TEST_LEGACY_SPECS_SEQUENCE, SpecsSequence],
}


def get_test_sequence(key: type) -> str:
    return TEST_SEQUENCES[key][SEQUENCE_KEY]


def get_test_sequence_type(key: type) -> type[AbstractBaseSequence]:
    return TEST_SEQUENCES[key][SEQUENCE_TYPE_KEY]


TEST_SEQUENCE_REGION_NAMES = ["New_Region", "New_Region1"]


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
            print(key)
            print(f" Region value from file: {r.__dict__[key]}")
            print(f" Expected value: {expected_region_values[key]}")
            assert r.__dict__[key] == expected_region_values[key]
        else:
            raise KeyError('key "' + key + '" is not in the expected values.')

    for key in expected_region_values.keys():
        assert r.__dict__.get(key) is not None


async def assert_read_configuration_has_expected_value(
    device: StandardReadable, key: str, expected_value
) -> None:
    read_config = await device.read_configuration()
    try:
        assert (
            read_config[device.name + device._child_name_separator + key]["value"]
            == expected_value
        )
    except KeyError as e:
        raise KeyError(
            f'Cannot find key "{key}" in read_configuration method. Following keys '
            + f"are {read_config.keys()}"
        ) from e
