from typing import Any

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.epics.motor import Motor

from dodal.devices.electron_analyser import ElectronAnalyserDetector
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseSequence,
    TAbstractAnalyserDriverIO,
    TAbstractBaseRegion,
    TAbstractBaseSequence,
)
from dodal.devices.electron_analyser.specs import (
    SpecsAnalyserDriverIO,
    SpecsSequence,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaSequence,
)
from tests.devices.unit_tests.electron_analyser.util import (
    ElectronAnalyserDetectorImpl,
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
    driver_class: type[TAbstractAnalyserDriverIO], RE: RunEngine
) -> TAbstractAnalyserDriverIO:
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
    driver_class: type[TAbstractAnalyserDriverIO],
    sequence_class: type[TAbstractBaseSequence],
    RE: RunEngine,
):
    det = ElectronAnalyserDetector(
        prefix="SIM:",
        driver_class=driver_class,
        sequence_class=sequence_class,
    )
    return det.load_sequence(get_test_sequence(driver_class))


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
