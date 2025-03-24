from typing import Any

import pytest
from tests.devices.unit_tests.electron_analyser.test_utils import (
    check_region_model_list_to_expected_values,
    is_list_of_custom_type,
)

from dodal.devices.electron_analyser.abstract_region import EnergyMode
from dodal.devices.electron_analyser.vgscienta_region import (
    AcquisitionMode,
    DetectorMode,
    Status,
    VGScientaRegion,
    VGScientaSequence,
)


@pytest.fixture
def sequence_file() -> str:
    return "vgscienta_sequence.seq"


@pytest.fixture
def sequence_class() -> type[VGScientaSequence]:
    return VGScientaSequence


@pytest.fixture
def expected_region_values() -> list[dict[str, Any]]:
    return [
        {
            "name": "New_Region",
            "enabled": True,
            "regionId": "_aQOmgPsmEe6w2YUF3bV-LA",
            "lensMode": "Angular56",
            "passEnergy": 5,
            "slices": 1,
            "iterations": 1,
            "acquisitionMode": AcquisitionMode.SWEPT,
            "excitationEnergySource": "source2",
            "energyMode": EnergyMode.KINETIC,
            "lowEnergy": 100.0,
            "highEnergy": 101.0,
            "fixEnergy": 9.0,
            "stepTime": 1.0,
            "totalSteps": 8.0,
            "totalTime": 8.0,
            "energyStep": 200.0,
            "exposureTime": 1.0,
            "firstXChannel": 1,
            "lastXChannel": 1000,
            "firstYChannel": 101,
            "lastYChannel": 800,
            "detectorMode": DetectorMode.ADC,
            "status": Status.READY,
        },
        {
            "name": "New_Region1",
            "enabled": False,
            "regionId": "_aQOmgPsmEe6w2YUF3GV-LL",
            "lensMode": "Angular45",
            "passEnergy": 10,
            "slices": 10,
            "iterations": 5,
            "acquisitionMode": AcquisitionMode.FIXED,
            "excitationEnergySource": "source1",
            "energyMode": EnergyMode.BINDING,
            "lowEnergy": 4899.5615,
            "highEnergy": 4900.4385,
            "fixEnergy": 4900.0,
            "stepTime": 0.882,
            "totalSteps": 1.0,
            "totalTime": 4.41,
            "energyStep": 0.877,
            "exposureTime": 1.0,
            "firstXChannel": 4,
            "lastXChannel": 990,
            "firstYChannel": 110,
            "lastYChannel": 795,
            "detectorMode": DetectorMode.PULSE_COUNTING,
            "status": Status.READY,
        },
    ]


@pytest.fixture
def expected_region_names(
    expected_region_values: list[dict[str, Any]],
) -> list[str]:
    names = []
    for expected_region_value in expected_region_values:
        names.append(expected_region_value["name"])
    return names


def test_get_expected_region_from_name(
    sequence: VGScientaSequence, expected_region_names: list[str]
) -> None:
    for name in expected_region_names:
        assert sequence.get_region_by_name(name) is not None
    assert sequence.get_region_by_name("region name should not be in sequence") is None


def test_sequence_get_expected_region_names(
    sequence: VGScientaSequence, expected_region_names: list[str]
) -> None:
    assert sequence.get_region_names() == expected_region_names


def test_sequence_get_expected_enabled_region_names(
    sequence: VGScientaSequence,
) -> None:
    assert sequence.get_enabled_region_names() == ["New_Region"]


def test_sequence_get_expected_region_type(sequence: VGScientaSequence) -> None:
    assert is_list_of_custom_type(sequence.regions, VGScientaRegion)
    assert is_list_of_custom_type(sequence.get_enabled_regions(), VGScientaRegion)


def test_sequence_get_expected_excitation_energy_source(
    sequence: VGScientaSequence,
) -> None:
    assert (
        sequence.get_excitation_energy_source_by_region(sequence.regions[0])
        == sequence.excitationEnergySources[1]
    )
    assert (
        sequence.get_excitation_energy_source_by_region(sequence.regions[1])
        == sequence.excitationEnergySources[0]
    )


def test_region_kinetic_and_binding_energy(sequence: VGScientaSequence) -> None:
    for r in sequence.regions:
        is_binding_energy = r.energyMode == EnergyMode.BINDING
        is_kinetic_energy = r.energyMode == EnergyMode.KINETIC

        assert r.is_binding_energy() == is_binding_energy
        assert r.is_binding_energy() != is_kinetic_energy
        assert r.is_kinetic_energy() == is_kinetic_energy
        assert r.is_kinetic_energy() != is_binding_energy


def test_sequence_file_loads_into_sequence_class(
    sequence: VGScientaSequence, expected_region_values: list[dict[str, Any]]
) -> None:
    check_region_model_list_to_expected_values(sequence.regions, expected_region_values)
