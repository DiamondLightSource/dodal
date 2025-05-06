from typing import Any

from ophyd_async.core import StandardReadable

from dodal.devices.electron_analyser.abstract import AbstractBaseRegion, EnergyMode
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector

TEST_VGSCIENTA = "VGSCIENTA"
TEST_SPECS = "SPECS"

SEQUENCE_FILE = "sequence_file"
DETECTOR = "detector"

TEST_VGSCIENTA_LOOKUP = {
    DETECTOR: VGScientaDetector,
    SEQUENCE_FILE: "vgscienta_sequence.seq",
}

TEST_SPECS_LOOKUP = {DETECTOR: SpecsDetector, SEQUENCE_FILE: "vgscienta_sequence.seq"}

TEST_VGSCIENTA_SEQUENCE = "vgscienta_sequence.seq"
TEST_SPECS_SEQUENCE = "specs_sequence.seq"
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
            assert r.__dict__[key] == expected_region_values[key]
        else:
            raise KeyError('key "' + key + '" is not in the expected values.')


async def assert_read_has_expected_value(
    device: StandardReadable, key: str, expected_value
) -> None:
    reading = await device.read()
    assert (
        reading[device.name + device._child_name_separator + key]["value"]
        == expected_value
    )


async def assert_read_configuration_has_expected_value(
    device: StandardReadable, key: str, expected_value
) -> None:
    read_config = await device.read_configuration()
    assert (
        read_config[device.name + device._child_name_separator + key]["value"]
        == expected_value
    )
