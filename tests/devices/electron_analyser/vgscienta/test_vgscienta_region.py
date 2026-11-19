from typing import Any

import pytest

from dodal.devices.beamlines.i09 import LensMode, PassEnergy
from dodal.devices.electron_analyser.base import EnergyMode
from dodal.devices.electron_analyser.vgscienta import (
    AcquisitionMode,
    DetectorMode,
    VGScientaRegion,
    VGScientaSequence,
)
from dodal.devices.selectable_source import SelectedSource
from tests.devices.electron_analyser.helper_util import (
    assert_region_has_expected_values,
    load_i09_vgscienta_test_seq,
)


@pytest.fixture
def expected_region_values() -> list[dict[str, Any]]:
    return [
        {
            "name": "New_Region",
            "enabled": True,
            "lens_mode": LensMode.ANGULAR56,
            "pass_energy": PassEnergy.E5,
            "slices": 1,
            "iterations": 1,
            "acquisition_mode": AcquisitionMode.SWEPT,
            "excitation_energy_source": SelectedSource.SOURCE2,
            "energy_mode": EnergyMode.KINETIC,
            "low_energy": 100.0,
            "high_energy": 101.0,
            "centre_energy": 9.0,
            "acquire_time": 1.0,
            "total_steps": 8.0,
            "total_time": 8.0,
            "energy_step": 0.2,
            "min_x": 1,
            "sensor_max_size_x": 1000,
            "min_y": 101,
            "sensor_max_size_y": 800,
            "detector_mode": DetectorMode.ADC,
        },
        {
            "name": "New_Region1",
            "enabled": False,
            "lens_mode": LensMode.ANGULAR45,
            "pass_energy": PassEnergy.E10,
            "slices": 10,
            "iterations": 5,
            "acquisition_mode": AcquisitionMode.FIXED,
            "excitation_energy_source": SelectedSource.SOURCE1,
            "energy_mode": EnergyMode.BINDING,
            "low_energy": 4899.5615,
            "high_energy": 4900.4385,
            "centre_energy": 4900.0,
            "acquire_time": 0.882,
            "total_steps": 1.0,
            "total_time": 4.41,
            "energy_step": 8.77e-4,
            "min_x": 4,
            "sensor_max_size_x": 990,
            "min_y": 110,
            "sensor_max_size_y": 795,
            "detector_mode": DetectorMode.PULSE_COUNTING,
        },
        {
            "name": "New_Region2",
            "enabled": True,
            "lens_mode": LensMode.ANGULAR45VUV,
            "pass_energy": PassEnergy.E20,
            "slices": 5,
            "iterations": 2,
            "acquisition_mode": AcquisitionMode.FIXED,
            "excitation_energy_source": SelectedSource.SOURCE1,
            "energy_mode": EnergyMode.KINETIC,
            "low_energy": 149.1905,
            "high_energy": 150.8095,
            "centre_energy": 150.0,
            "acquire_time": 0.0625,
            "total_steps": 1.0,
            "total_time": 0.126,
            "energy_step": 0.001619,
            "min_x": 1,
            "sensor_max_size_x": 1000,
            "min_y": 101,
            "sensor_max_size_y": 800,
            "detector_mode": DetectorMode.ADC,
        },
    ]


def test_load_sequence_using_alias_field_names_has_expected_values(
    expected_region_values: list[dict[str, Any]],
) -> None:
    for i, r in zip(
        load_i09_vgscienta_test_seq().regions, expected_region_values, strict=True
    ):
        assert_region_has_expected_values(i, r)


def test_region_loads_using_field_names_has_expected_values(
    expected_region_values: list[dict[str, Any]],
) -> None:
    for expected_region in expected_region_values:
        r = VGScientaRegion[LensMode, PassEnergy].model_validate(expected_region)
        assert_region_has_expected_values(r, expected_region)
    seq = VGScientaSequence[LensMode, PassEnergy].model_validate(
        {"regions": expected_region_values}
    )
    for r, expected_r in zip(seq.regions, expected_region_values, strict=True):
        assert_region_has_expected_values(r, expected_r)
