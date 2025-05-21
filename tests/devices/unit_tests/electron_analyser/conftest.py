from typing import Any

import pytest
from ophyd_async.core import init_devices

from dodal.devices.electron_analyser.abstract import (
    AbstractBaseSequence,
    TAbstractAnalyserDriverIO,
    TAbstractBaseRegion,
)
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaDetector,
)

ElectronAnalyserDetectorImpl = SpecsDetector | VGScientaDetector


@pytest.fixture
async def sim_driver(
    driver_class: type[TAbstractAnalyserDriverIO],
) -> TAbstractAnalyserDriverIO:
    async with init_devices(mock=True, connect=True):
        sim_driver = driver_class(
            prefix="TEST:",
            name="sim_driver",
        )
    return sim_driver


@pytest.fixture
async def sim_detector(
    detector_class: type[ElectronAnalyserDetectorImpl],
) -> ElectronAnalyserDetectorImpl:
    async with init_devices(mock=True, connect=True):
        sim_detector = detector_class(
            prefix="TEST:",
            name="sim_detector",
        )
    return sim_detector


@pytest.fixture
def region(
    request: pytest.FixtureRequest, sequence: AbstractBaseSequence[TAbstractBaseRegion]
) -> TAbstractBaseRegion:
    region = sequence.get_region_by_name(request.param)
    if region is None:
        raise ValueError("Region " + request.param + " is not found.")
    return region


# ToDo - This needs to come from a device
# https://github.com/DiamondLightSource/dodal/issues/1224
@pytest.fixture
def excitation_energy() -> float:
    return 0


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
