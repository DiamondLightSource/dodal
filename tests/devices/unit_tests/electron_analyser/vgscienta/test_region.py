from typing import Any

import pytest

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.abstract import TAbstractBaseRegion
from dodal.devices.electron_analyser.types import EnergyMode
from dodal.devices.electron_analyser.vgscienta import VGScientaRegion, VGScientaSequence
from dodal.devices.electron_analyser.vgscienta.region import (
    AcquisitionMode,
    DetectorMode,
    Status,
    VGScientaRegion,
    VGScientaSequence,
)
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_VGSCIENTA_SEQUENCE,
    assert_region_has_expected_values,
    assert_region_kinetic_and_binding_energy,
)


@pytest.fixture
def sequence() -> VGScientaSequence:
    return load_json_file_to_class(VGScientaSequence, TEST_VGSCIENTA_SEQUENCE)


@pytest.fixture
def expected_region_class() -> type[VGScientaRegion]:
    return VGScientaRegion


@pytest.fixture
def expected_region_values() -> list[dict[str, Any]]:
    return [
        {
            "name": "New_Region",
            "enabled": True,
            "id": "_aQOmgPsmEe6w2YUF3bV-LA",
            "lens_mode": "Angular56",
            "pass_energy": 5,
            "slices": 1,
            "iterations": 1,
            "acquisition_mode": AcquisitionMode.SWEPT,
            "excitation_energy_source": "source2",
            "energy_mode": EnergyMode.KINETIC,
            "low_energy": 100.0,
            "high_energy": 101.0,
            "fix_energy": 9.0,
            "step_time": 1.0,
            "total_steps": 8.0,
            "total_time": 8.0,
            "energy_step": 0.2,
            "exposure_time": 1.0,
            "first_x_channel": 1,
            "last_x_channel": 1000,
            "first_y_channel": 101,
            "last_y_channel": 800,
            "detector_mode": DetectorMode.ADC,
            "status": Status.READY,
        },
        {
            "name": "New_Region1",
            "enabled": False,
            "id": "_aQOmgPsmEe6w2YUF3GV-LL",
            "lens_mode": "Angular45",
            "pass_energy": 10,
            "slices": 10,
            "iterations": 5,
            "acquisition_mode": AcquisitionMode.FIXED,
            "excitation_energy_source": "source1",
            "energy_mode": EnergyMode.BINDING,
            "low_energy": 4899.5615,
            "high_energy": 4900.4385,
            "fix_energy": 4900.0,
            "step_time": 0.882,
            "total_steps": 1.0,
            "total_time": 4.41,
            "energy_step": 8.77e-4,
            "exposure_time": 1.0,
            "first_x_channel": 4,
            "last_x_channel": 990,
            "first_y_channel": 110,
            "last_y_channel": 795,
            "detector_mode": DetectorMode.PULSE_COUNTING,
            "status": Status.READY,
        },
    ]


def test_sequence_get_expected_region_from_name(
    sequence: VGScientaSequence, expected_region_names: list[str]
) -> None:
    for name in expected_region_names:
        assert sequence.get_region_by_name(name) is not None
    assert sequence.get_region_by_name("region name should not be in sequence") is None


def test_sequence_get_expected_region_type(
    sequence: VGScientaSequence,
    expected_region_class: type[TAbstractBaseRegion],
) -> None:
    regions = sequence.regions
    enabled_regions = sequence.get_enabled_regions()
    assert isinstance(regions, list) and all(
        isinstance(r, expected_region_class) for r in regions
    )
    assert isinstance(enabled_regions, list) and all(
        isinstance(r, expected_region_class) for r in enabled_regions
    )


def test_sequence_get_expected_region_names(
    sequence: VGScientaSequence, expected_region_names: list[str]
) -> None:
    assert sequence.get_region_names() == expected_region_names


def test_sequence_get_expected_enabled_region_names(
    sequence: VGScientaSequence, expected_enabled_region_names: list[str]
) -> None:
    assert sequence.get_enabled_region_names() == expected_enabled_region_names


def test_sequence_get_expected_excitation_energy_source(
    sequence: VGScientaSequence,
) -> None:
    assert (
        sequence.get_excitation_energy_source_by_region(sequence.regions[0])
        == sequence.excitation_energy_sources[1]
    )
    assert (
        sequence.get_excitation_energy_source_by_region(sequence.regions[1])
        == sequence.excitation_energy_sources[0]
    )
    with pytest.raises(ValueError):
        sequence.get_excitation_energy_source_by_region(
            VGScientaRegion(excitation_energy_source="invalid_source")
        )


def test_region_kinetic_and_binding_energy(sequence: VGScientaSequence) -> None:
    for r in sequence.regions:
        assert_region_kinetic_and_binding_energy(r)


def test_file_loads_into_class_with_expected_values(
    sequence: VGScientaSequence,
    expected_region_values: list[dict[str, Any]],
) -> None:
    assert len(sequence.regions) == len(expected_region_values)
    for i, r in enumerate(sequence.regions):
        assert_region_has_expected_values(r, expected_region_values[i])
