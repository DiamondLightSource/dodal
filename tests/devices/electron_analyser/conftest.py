from typing import Any

import pytest
from ophyd_async.core import init_devices

from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorWithDSpacing,
    PitchAndRollCrystal,
    StationaryCrystal,
)
from dodal.devices.electron_analyser.base import (
    AbstractBaseRegion,
    DualEnergySource,
    EnergySource,
    GenericSequence,
    SequenceLoader,
)
from dodal.devices.i09 import Grating
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.selectable_source import SourceSelector
from tests.devices.electron_analyser.helper_util import get_test_sequence


@pytest.fixture
async def source_selector() -> SourceSelector:
    async with init_devices(mock=True):
        source_selector = SourceSelector()
    return source_selector


@pytest.fixture
async def single_energy_source() -> EnergySource:
    async with init_devices(mock=True):
        dcm = DoubleCrystalMonochromatorWithDSpacing(
            "DCM:", PitchAndRollCrystal, StationaryCrystal
        )
    await dcm.energy_in_keV.set(2.2)
    async with init_devices(mock=True):
        dcm_energy_source = EnergySource(dcm.energy_in_eV)

    return dcm_energy_source


@pytest.fixture
async def dual_energy_source(source_selector: SourceSelector) -> DualEnergySource:
    async with init_devices(mock=True):
        dcm = DoubleCrystalMonochromatorWithDSpacing(
            "DCM:", PitchAndRollCrystal, StationaryCrystal
        )
        pgm = PlaneGratingMonochromator("PGM:", Grating)
    await dcm.energy_in_keV.set(2.2)
    await pgm.energy.set(500)
    async with init_devices(mock=True):
        dual_energy_source = DualEnergySource(
            source1=dcm.energy_in_eV,
            source2=pgm.energy.user_readback,
            selected_source=source_selector.selected_source,
        )
    return dual_energy_source


@pytest.fixture
async def sequence(
    sequence_loader: SequenceLoader[GenericSequence],
) -> GenericSequence:
    filename = get_test_sequence(sequence_loader._sequence_class)
    await sequence_loader.set(filename)
    if sequence_loader.sequence is None:
        raise ValueError(f"Sequence is None when set to file: {filename}.")
    return sequence_loader.sequence


@pytest.fixture
async def region(
    request: pytest.FixtureRequest,
    sequence: GenericSequence,
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
