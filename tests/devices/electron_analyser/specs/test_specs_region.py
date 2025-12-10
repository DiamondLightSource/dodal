from typing import Any

import pytest

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.b07 import LensMode, PsuMode
from dodal.devices.electron_analyser import EnergyMode, SelectedSource
from dodal.devices.electron_analyser.specs import (
    AcquisitionMode,
    SpecsSequence,
)
from tests.devices.electron_analyser.helper_util import (
    assert_region_has_expected_values,
    get_test_sequence,
)


@pytest.fixture
def sequence() -> SpecsSequence[LensMode, PsuMode]:
    seq = SpecsSequence[LensMode, PsuMode]
    return load_json_file_to_class(seq, get_test_sequence(seq))


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
            "acquire_time": 1.0,
            "enabled": False,
            "energy_mode": EnergyMode.KINETIC,
            "values": 1,
            "slices": 100,
            "centre_energy": 0.0,
            "estimated_time_in_ms": 0.0,
            "excitation_energy_source": SelectedSource.SOURCE1,
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
            "estimated_time_in_ms": 13718.0,
            "excitation_energy_source": SelectedSource.SOURCE1,
        },
        {
            "name": "New_Region2",
            "acquisition_mode": AcquisitionMode.FIXED_ENERGY,
            "psu_mode": PsuMode.V400,
            "lens_mode": LensMode.HIGH_ANGULAR_DISPERSION,
            "low_energy": 299.665,
            "high_energy": 300.335,
            "energy_step": 0.4,
            "pass_energy": 5.0,
            "iterations": 1,
            "acquire_time": 1.0,
            "enabled": True,
            "energy_mode": EnergyMode.KINETIC,
            "values": 2,
            "slices": 100,
            "centre_energy": 300.0,
            "estimated_time_in_ms": 4125.0,
            "excitation_energy_source": SelectedSource.SOURCE1,
        },
    ]


def test_sequence_get_expected_enabled_region_names(
    sequence: SpecsSequence[LensMode, PsuMode],
    expected_enabled_region_names: list[str],
) -> None:
    assert sequence.get_enabled_region_names() == expected_enabled_region_names
    for i, region in enumerate(sequence.get_enabled_regions()):
        assert region.name == expected_enabled_region_names[i]


def test_file_loads_into_class_with_expected_values(
    sequence: SpecsSequence[LensMode, PsuMode],
    expected_region_values: list[dict[str, Any]],
) -> None:
    assert len(sequence.regions) == len(expected_region_values)
    for i, r in enumerate(sequence.regions):
        assert_region_has_expected_values(r, expected_region_values[i])
