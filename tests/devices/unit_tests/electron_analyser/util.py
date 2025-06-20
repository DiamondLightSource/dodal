import os
from typing import Any
from unittest.mock import ANY

from bluesky import plan_stubs as bps
from ophyd_async.epics.motor import Motor

from dodal.devices.electron_analyser import EnergyMode
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.specs import (
    SpecsAnalyserDriverIO,
    SpecsDetector,
    SpecsSequence,
)
from dodal.devices.electron_analyser.specs.enums import (
    AcquisitionMode as SpecsAcquisitionMode,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaDetector,
    VGScientaSequence,
)
from dodal.devices.electron_analyser.vgscienta.enums import (
    AcquisitionMode as VGAcquisitionsMode,
)
from dodal.devices.electron_analyser.vgscienta.enums import DetectorMode

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


def configure_driver_with_region(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    sim_energy_source: Motor,
):
    yield from bps.prepare(sim_driver, sim_energy_source)
    yield from bps.mv(sim_driver, region)


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
            assert r.__dict__[key] == expected_region_values[key]
        else:
            raise KeyError('key "' + key + '" is not in the expected values.')

    for key in expected_region_values.keys():
        assert r.__dict__.get(key) is not None


def expected_config(
    driver: AbstractAnalyserDriverIO, region: AbstractBaseRegion
) -> dict[str, dict[str, Any]]:
    driver_type = type(driver)
    region_name = region.name
    if driver_type is VGScientaAnalyserDriverIO:
        match region_name:
            case "New_Region":
                return {
                    "sim_driver-slices": {"value": 1},
                    "sim_driver-acquisition_mode": {"value": VGAcquisitionsMode.SWEPT},
                    "sim_driver-angle_axis": {"value": []},
                    "sim_driver-binding_energy_axis": {"value": []},
                    "sim_driver-centre_energy": {"value": 9.0},
                    "sim_driver-detector_mode": {"value": DetectorMode.ADC},
                    "sim_driver-energy_axis": {"value": []},
                    "sim_driver-energy_mode": {"value": EnergyMode.KINETIC},
                    "sim_driver-energy_step": {"value": 0.2},
                    "sim_driver-excitation_energy_source": {"value": "sim_driver"},
                    "sim_driver-first_x_channel": {"value": 1},
                    "sim_driver-first_y_channel": {"value": 101},
                    "sim_driver-high_energy": {"value": 101.0},
                    "sim_driver-iterations": {"value": 1},
                    "sim_driver-lens_mode": {"value": "Angular56"},
                    "sim_driver-low_energy": {"value": 100.0},
                    "sim_driver-pass_energy": {"value": "5"},
                    "sim_driver-region_name": {"value": "New_Region"},
                    "sim_driver-step_time": {"value": 0.0},
                    "sim_driver-total_steps": {"value": 0},
                    "sim_driver-total_time": {"value": 0.0},
                    "sim_driver-x_channel_size": {"value": 1000},
                    "sim_driver-y_channel_size": {"value": 700},
                }
            case "New_Region1":
                return {
                    "sim_driver-slices": {"value": 10},
                    "sim_driver-acquisition_mode": {"value": VGAcquisitionsMode.FIXED},
                    "sim_driver-angle_axis": {"value": []},
                    "sim_driver-binding_energy_axis": {"value": []},
                    "sim_driver-centre_energy": {"value": -4900.0},
                    "sim_driver-detector_mode": {"value": DetectorMode.PULSE_COUNTING},
                    "sim_driver-energy_axis": {"value": []},
                    "sim_driver-energy_mode": {"value": EnergyMode.BINDING},
                    "sim_driver-energy_step": {"value": 0.000877},
                    "sim_driver-excitation_energy_source": {"value": "sim_driver"},
                    "sim_driver-first_x_channel": {"value": 4},
                    "sim_driver-first_y_channel": {"value": 110},
                    "sim_driver-high_energy": {"value": -4900.4385},
                    "sim_driver-iterations": {"value": 5},
                    "sim_driver-lens_mode": {"value": "Angular45"},
                    "sim_driver-low_energy": {"value": -4899.5615},
                    "sim_driver-pass_energy": {"value": "10"},
                    "sim_driver-region_name": {"value": "New_Region1"},
                    "sim_driver-step_time": {"value": 0.0},
                    "sim_driver-total_steps": {"value": 0},
                    "sim_driver-total_time": {"value": 0.0},
                    "sim_driver-x_channel_size": {"value": 987},
                    "sim_driver-y_channel_size": {"value": 686},
                }
            case _:
                raise ValueError(f"{region_name} is not expected by {driver_type}")
    elif driver_type is SpecsAnalyserDriverIO:
        match region_name:
            case "New_Region":
                return {
                    "sim_driver-slices": {"value": 100},
                    "sim_driver-acquisition_mode": {
                        "value": SpecsAcquisitionMode.FIXED_TRANSMISSION
                    },
                    "sim_driver-angle_axis": {"value": ANY},
                    "sim_driver-binding_energy_axis": {"value": ANY},
                    "sim_driver-centre_energy": {"value": 0.0},
                    "sim_driver-energy_axis": {"value": ANY},
                    "sim_driver-energy_mode": {"value": EnergyMode.KINETIC},
                    "sim_driver-energy_step": {"value": 0.0},
                    "sim_driver-excitation_energy_source": {"value": "sim_driver"},
                    "sim_driver-high_energy": {"value": 850.0},
                    "sim_driver-iterations": {"value": 1},
                    "sim_driver-lens_mode": {"value": "SmallArea"},
                    "sim_driver-low_energy": {"value": 800.0},
                    "sim_driver-max_angle_axis": {"value": 0.0},
                    "sim_driver-min_angle_axis": {"value": 0.0},
                    "sim_driver-pass_energy": {"value": 5.0},
                    "sim_driver-psu_mode": {"value": "3.5kV"},
                    "sim_driver-region_name": {"value": "New_Region"},
                    "sim_driver-snapshot_values": {"value": 1},
                    "sim_driver-step_time": {"value": 0.0},
                    "sim_driver-total_steps": {"value": 0},
                    "sim_driver-total_time": {"value": 0.0},
                }
            case "New_Region1":
                return {
                    "sim_driver-slices": {"value": 110},
                    "sim_driver-acquisition_mode": {
                        "value": SpecsAcquisitionMode.SNAPSHOT
                    },
                    "sim_driver-angle_axis": {"value": ANY},
                    "sim_driver-binding_energy_axis": {"value": ANY},
                    "sim_driver-centre_energy": {"value": 0.0},
                    "sim_driver-energy_axis": {"value": ANY},
                    "sim_driver-energy_mode": {"value": EnergyMode.BINDING},
                    "sim_driver-energy_step": {"value": 0.0},
                    "sim_driver-excitation_energy_source": {"value": "sim_driver"},
                    "sim_driver-high_energy": {"value": -600.134},
                    "sim_driver-iterations": {"value": 5},
                    "sim_driver-lens_mode": {"value": "LargeArea"},
                    "sim_driver-low_energy": {"value": -599.866},
                    "sim_driver-max_angle_axis": {"value": 0.0},
                    "sim_driver-min_angle_axis": {"value": 0.0},
                    "sim_driver-pass_energy": {"value": 2.0},
                    "sim_driver-psu_mode": {"value": "1.5kV"},
                    "sim_driver-region_name": {"value": "New_Region1"},
                    "sim_driver-snapshot_values": {"value": 1},
                    "sim_driver-step_time": {"value": 0.0},
                    "sim_driver-total_steps": {"value": 0},
                    "sim_driver-total_time": {"value": 0.0},
                }
            case _:
                raise ValueError(f"{region_name} is not expected by {driver_type}")
    else:
        raise ValueError(f"Unknown Driver class {driver_type}")
