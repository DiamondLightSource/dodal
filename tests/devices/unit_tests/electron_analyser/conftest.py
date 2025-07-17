from typing import Any, get_args

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import SignalR, init_devices
from ophyd_async.sim import SimMotor

from dodal.devices.electron_analyser import (
    ElectronAnalyserDetector,
    ElectronAnalyserDetectorImpl,
    ElectronAnalyserDriverImpl,
)
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    AbstractBaseSequence,
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
    get_test_sequence,
)


@pytest.fixture
async def pgm_energy(RE: RunEngine) -> SimMotor:
    return SimMotor("pgm_energy")


@pytest.fixture
async def dcm_energy(RE: RunEngine) -> SimMotor:
    return SimMotor("dcm_energy")


@pytest.fixture
async def energy_sources(
    dcm_energy: SimMotor, pgm_energy: SimMotor
) -> dict[str, SignalR[float]]:
    return {"source1": dcm_energy.user_readback, "source2": pgm_energy.user_readback}


@pytest.fixture
async def sim_detector(
    detector_class: type[ElectronAnalyserDetectorImpl],
    energy_sources: dict[str, SignalR[float]],
    RE: RunEngine,
) -> ElectronAnalyserDetectorImpl:
    lens_mode_class = get_args(detector_class)[0]
    async with init_devices(mock=True, connect=True):
        sim_detector = detector_class("TEST:", lens_mode_class, energy_sources)
    return sim_detector


@pytest.fixture
async def sim_driver(
    driver_class: type[ElectronAnalyserDriverImpl],
    energy_sources: dict[str, SignalR[float]],
    RE: RunEngine,
) -> ElectronAnalyserDriverImpl:
    lens_mode_class = get_args(driver_class)[0]
    async with init_devices(mock=True, connect=True):
        sim_driver = driver_class(
            "TEST:",
            lens_mode_class,
            energy_sources,
        )
    return sim_driver


@pytest.fixture
def sequence_class(
    sim_driver: AbstractAnalyserDriverIO,
) -> type[AbstractBaseSequence]:
    # We must include the lens mode type here, otherwise the sequence file can't be
    # loaded as pydantic won't be able to resolve the lens mode enum.
    if isinstance(sim_driver, VGScientaAnalyserDriverIO):
        return VGScientaSequence[sim_driver.lens_mode_type]
    elif isinstance(sim_driver, SpecsAnalyserDriverIO):
        return SpecsSequence[sim_driver.lens_mode_type]
    raise ValueError("class " + str(sim_driver) + " not recognised")


@pytest.fixture
def sequence(
    sim_driver: AbstractAnalyserDriverIO,
    sequence_class: type[TAbstractBaseSequence],
    RE: RunEngine,
) -> AbstractBaseSequence:
    det = ElectronAnalyserDetector(
        driver=sim_driver,
        sequence_class=sequence_class,
    )
    return det.load_sequence(get_test_sequence(type(sim_driver)))


@pytest.fixture
def region(
    request: pytest.FixtureRequest,
    sequence: AbstractBaseSequence,
) -> AbstractBaseRegion:
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
