from typing import Any
from unittest.mock import ANY

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.epics.motor import Motor

from dodal.devices.electron_analyser import (
    ElectronAnalyserDetector,
    ElectronAnalyserDetectorImpl,
    ElectronAnalyserDriverImpl,
    EnergyMode,
)
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseSequence,
    TAbstractBaseRegion,
    TAbstractBaseSequence,
)
from dodal.devices.electron_analyser.abstract.base_region import AbstractBaseRegion
from dodal.devices.electron_analyser.specs import (
    SpecsAnalyserDriverIO,
    SpecsSequence,
)
from dodal.devices.electron_analyser.specs.enums import (
    AcquisitionMode as SpecsAcquisitionMode,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaSequence,
)
from dodal.devices.electron_analyser.vgscienta.enums import (
    AcquisitionMode as VGAcquisitionsMode,
)
from dodal.devices.electron_analyser.vgscienta.enums import DetectorMode
from tests.devices.unit_tests.electron_analyser.util import (
    get_test_sequence,
)


@pytest.fixture
async def sim_detector(
    detector_class: type[ElectronAnalyserDetectorImpl], RE: RunEngine
) -> ElectronAnalyserDetectorImpl:
    async with init_devices(mock=True, connect=True):
        sim_detector = detector_class(
            prefix="TEST:",
        )
    return sim_detector


@pytest.fixture
async def sim_driver(
    driver_class: type[ElectronAnalyserDriverImpl], RE: RunEngine
) -> ElectronAnalyserDriverImpl:
    async with init_devices(mock=True, connect=True):
        sim_driver = driver_class(
            prefix="TEST:",
        )
    return sim_driver


@pytest.fixture
async def sim_energy_source(RE: RunEngine) -> Motor:
    async with init_devices(mock=True, connect=True):
        sim_driver = Motor(
            prefix="TEST:",
        )
    return sim_driver


@pytest.fixture
def sequence_class(
    driver_class: type[AbstractAnalyserDriverIO],
) -> type[AbstractBaseSequence]:
    if driver_class == VGScientaAnalyserDriverIO:
        return VGScientaSequence
    elif driver_class == SpecsAnalyserDriverIO:
        return SpecsSequence
    raise ValueError("class " + str(driver_class) + " not recognised")


@pytest.fixture
def sequence(
    sim_driver: AbstractAnalyserDriverIO,
    sequence_class: type[TAbstractBaseSequence],
    RE: RunEngine,
):
    det = ElectronAnalyserDetector(
        prefix="SIM:",
        driver=sim_driver,
        sequence_class=sequence_class,
    )
    return det.load_sequence(get_test_sequence(type(sim_driver)))


@pytest.fixture
def region(
    request: pytest.FixtureRequest, sequence: AbstractBaseSequence[TAbstractBaseRegion]
) -> TAbstractBaseRegion:
    region = sequence.get_region_by_name(request.param)
    if region is None:
        raise ValueError("Region " + request.param + " is not found.")
    return region


@pytest.fixture
def expected_region_names(expected_region_values: list[dict[str, Any]]) -> list[str]:
    names = []
    for expected_region_value in expected_region_values:
        names.append(expected_region_value["name"])
    return names


@pytest.fixture
def expected_enabled_region_names(
    expected_region_values: list[dict[str, Any]],
) -> list[str]:
    names = []
    for expected_region_value in expected_region_values:
        if expected_region_value["enabled"]:
            names.append(expected_region_value["name"])
    return names


@pytest.fixture
def expected_config(
    sim_driver: VGScientaAnalyserDriverIO | SpecsAnalyserDriverIO,
    region: AbstractBaseRegion,
) -> dict[str, dict[str, Any]]:
    region_name = region.name
    if type(sim_driver) is VGScientaAnalyserDriverIO:
        if region_name == "New_Region":
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
    if region_name == "New_Region":
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
    return {
        "sim_driver-slices": {"value": 110},
        "sim_driver-acquisition_mode": {"value": SpecsAcquisitionMode.SNAPSHOT},
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
