import os
from typing import Any

import pytest
from ophyd_async.core import init_devices

from dodal.devices.electron_analyser import TElectronAnalyserDetectorImpl
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    AbstractBaseSequence,
    AbstractElectronAnalyserDetector,
    TAbstractAnalyserDriverIO,
    TAbstractBaseRegion,
    TAbstractBaseSequence,
)
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO, SpecsDetector
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaDetector,
    VGScientaRegion,
    VGScientaSequence,
)
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_SPECS_SEQUENCE,
    TEST_VGSCIENTA_SEQUENCE,
)

TEST_DATA_PATH = "tests/test_data/electron_analyser/"


@pytest.fixture
def sequence_file_path(sequence_file: str) -> str:
    return os.path.join(TEST_DATA_PATH, sequence_file)


@pytest.fixture
def sequence_file(analyser_driver_class: type[AbstractAnalyserDriverIO]) -> str:
    if analyser_driver_class == VGScientaAnalyserDriverIO:
        return TEST_VGSCIENTA_SEQUENCE
    elif analyser_driver_class == SpecsAnalyserDriverIO:
        return TEST_SPECS_SEQUENCE
    raise Exception


@pytest.fixture
async def sim_analyser_driver(
    analyser_driver_class: type[TAbstractAnalyserDriverIO],
) -> TAbstractAnalyserDriverIO:
    async with init_devices(mock=True, connect=True):
        sim_analyser_driver = analyser_driver_class(
            prefix="sim_analyser_driver:",
            name="analyser_driver",
        )
    return sim_analyser_driver


@pytest.fixture
async def sim_analyser(
    sim_analyser_driver: AbstractAnalyserDriverIO,
) -> TElectronAnalyserDetectorImpl:
    if isinstance(sim_analyser_driver, VGScientaAnalyserDriverIO):
        async with init_devices(mock=True, connect=True):
            sim_analyser = VGScientaDetector(
                name="analyser", driver=sim_analyser_driver
            )
        return sim_analyser
    elif isinstance(sim_analyser_driver, SpecsAnalyserDriverIO):
        async with init_devices(mock=True, connect=True):
            sim_analyser = SpecsDetector(name="analyser", driver=sim_analyser_driver)
        return sim_analyser

    raise Exception(
        f"Type {type(sim_analyser_driver)} is not supported for sim_analyser."
    )


@pytest.fixture
def sequence(
    sim_analyser: AbstractElectronAnalyserDetector[
        TAbstractAnalyserDriverIO, TAbstractBaseSequence, TAbstractBaseRegion
    ],
    sequence_file_path: str,
) -> TAbstractBaseSequence:
    return sim_analyser.load_sequence(sequence_file_path)


@pytest.fixture
def region(
    request: pytest.FixtureRequest, sequence: AbstractBaseSequence[TAbstractBaseRegion]
) -> TAbstractBaseRegion:
    region = sequence.get_region_by_name(request.param)
    if region is None:
        raise ValueError("Region " + request.param + " is not found.")
    return region


@pytest.fixture
def excitation_energy(
    sequence: AbstractBaseSequence, region: AbstractBaseRegion
) -> float:
    if isinstance(sequence, VGScientaSequence) and isinstance(region, VGScientaRegion):
        return sequence.get_excitation_energy_source_by_region(region).value
    return 1000


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
