import os
from typing import Any

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.abstract_analyser_controller import (
    TAbstractAnalyserController,
)
from dodal.devices.electron_analyser.abstract_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
    TAbstractBaseRegion,
    TAbstractBaseSequence,
)
from dodal.devices.electron_analyser.vgscienta_region import (
    VGScientaRegion,
    VGScientaSequence,
)

TEST_DATA_PATH = "tests/test_data/electron_analyser/"


@pytest.fixture
def sequence_file_path(sequence_file: str) -> str:
    return os.path.join(TEST_DATA_PATH, sequence_file)


@pytest.fixture
def sequence(
    sequence_class: type[TAbstractBaseSequence], sequence_file_path: str
) -> TAbstractBaseSequence:
    return load_json_file_to_class(sequence_class, sequence_file_path)


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


@pytest.fixture
async def sim_analyser(
    analyser_type: type[TAbstractAnalyserController],
) -> TAbstractAnalyserController:
    async with init_devices(mock=True):
        sim_analyser = analyser_type(
            prefix="sim_analyser",
            name="analyser",
        )
    return sim_analyser


@pytest.fixture
def RE() -> RunEngine:
    return RunEngine()
