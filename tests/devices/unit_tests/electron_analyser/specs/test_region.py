from typing import Any

import pytest

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.b07 import LensMode, PsuMode
from dodal.devices.electron_analyser import EnergyMode
from dodal.devices.electron_analyser.abstract.base_region import TAbstractBaseRegion
from dodal.devices.electron_analyser.specs import (
    AcquisitionMode,
    SpecsRegion,
    SpecsSequence,
)
from tests.devices.unit_tests.electron_analyser.util import (
    TEST_LEGACY_SPECS_SEQUENCE,
    TEST_NEW_SPECS_SEQUENCE,
    assert_region_has_expected_values,
    assert_region_kinetic_and_binding_energy,
)


@pytest.fixture
def sequence() -> SpecsSequence[LensMode]:
    return load_json_file_to_class(SpecsSequence[LensMode, PsuMode], TEST_LEGACY_SPECS_SEQUENCE)


@pytest.fixture
def new_sequence() -> SpecsSequence[LensMode]:
    return load_json_file_to_class(SpecsSequence[LensMode, PsuMode], TEST_NEW_SPECS_SEQUENCE)


@pytest.fixture
def expected_region_class() -> type[SpecsRegion[LensMode, PsuMode]]:
    return SpecsRegion[LensMode, PsuMode]


@pytest.fixture
def expected_region_values() -> list[dict[str, Any]]:
    return [
        {
            "name": "New_Region",
            "acquisition_mode": AcquisitionMode.FIXED_TRANSMISSION,
            "psu_mode": PsuMode.V3500,
            "lens_mode": LensMode.SMALL_AREA,
            "low_energy": 800.0,
            "high_energy": 850.0,
            "energy_step": 0.1,
            "pass_energy": 5.0,
            "iterations": 1,
            "acquire_time": 0.25,
            "enabled": False,
            "energy_mode": EnergyMode.KINETIC,
            "values": 1,
            "slices": 100,
            "centre_energy": 0.0,
            "estimated_time_in_ms": 0,
            "excitation_energy_source": "source1",
        },
        {
            "name": "New_Region1",
            "acquisition_mode": AcquisitionMode.SNAPSHOT,
            "psu_mode": PsuMode.V1500,
            "lens_mode": LensMode.LARGE_AREA,
            "low_energy": 599.866,
            "high_energy": 600.134,
            "energy_step": 0.2680000000000291,
            "pass_energy": 2.0,
            "iterations": 5,
            "acquire_time": 2.0,
            "enabled": True,
            "energy_mode": EnergyMode.BINDING,
            "values": 1,
            "slices": 110,
            "centre_energy": 0.0,
            "estimated_time_in_ms": 13718,
            "excitation_energy_source": "source1",
        },
    ]


def test_sequence_get_expected_region_from_name(
    sequence: SpecsSequence[LensMode, PsuMode], expected_region_names: list[str]
) -> None:
    for name in expected_region_names:
        assert sequence.get_region_by_name(name) is not None
    assert sequence.get_region_by_name("region name should not be in sequence") is None


def test_sequence_get_expected_region_type(
    sequence: SpecsSequence[LensMode, PsuMode],
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
    sequence: SpecsSequence[LensMode, PsuMode], expected_region_names: list[str]
) -> None:
    assert sequence.get_region_names() == expected_region_names


def test_sequence_get_expected_enabled_region_names(
    sequence: SpecsSequence[LensMode, PsuMode], expected_enabled_region_names: list[str]
) -> None:
    assert sequence.get_enabled_region_names() == expected_enabled_region_names


def test_region_kinetic_and_binding_energy(
    sequence: SpecsSequence[LensMode, PsuMode],
) -> None:
    for r in sequence.regions:
        assert_region_kinetic_and_binding_energy(r)


def test_legacy_file_loads_into_class_with_expected_values(
    sequence: SpecsSequence[LensMode, PsuMode],
    expected_region_values: list[dict[str, Any]],
) -> None:
    assert len(sequence.regions) == len(expected_region_values)
    for i, r in enumerate(sequence.regions):
        assert_region_has_expected_values(r, expected_region_values[i])


def test_new_file_loads_into_class_with_expected_values(
    new_sequence: SpecsSequence[LensMode, PsuMode],
    expected_region_values: list[dict[str, Any]],
) -> None:
    assert len(new_sequence.regions) == len(expected_region_values)
    for i, r in enumerate(new_sequence.regions):
        assert_region_has_expected_values(r, expected_region_values[i])
