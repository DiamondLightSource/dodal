from typing import Any

import pytest
from ophyd_async.core import init_devices

from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorWithDSpacing,
    PitchAndRollCrystal,
    StationaryCrystal,
)
from dodal.devices.electron_analyser import (
    DualEnergySource,
    ElectronAnalyserDetector,
    EnergySource,
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
from dodal.devices.i09 import Grating
from dodal.devices.pgm import PlaneGratingMonochromator
from tests.devices.electron_analyser.helper_util import (
    get_test_sequence,
)


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
async def dual_energy_source() -> DualEnergySource:
    async with init_devices(mock=True):
        dcm = DoubleCrystalMonochromatorWithDSpacing(
            "DCM:", PitchAndRollCrystal, StationaryCrystal
        )
        pgm = PlaneGratingMonochromator("PGM:", Grating)
    await dcm.energy_in_keV.set(2.2)
    await pgm.energy.set(500)
    async with init_devices(mock=True):
        dual_energy_source = DualEnergySource(
            source1=dcm.energy_in_eV, source2=pgm.energy.user_readback
        )
    return dual_energy_source


@pytest.fixture
def sequence_class(
    sim_driver: AbstractAnalyserDriverIO,
) -> type[AbstractBaseSequence]:
    # We must include the pass energy, lens and psu mode types here, otherwise the
    # sequence file can't be loaded as pydantic won't be able to resolve the enums.
    if isinstance(sim_driver, VGScientaAnalyserDriverIO):
        return VGScientaSequence[
            sim_driver.lens_mode_type,
            sim_driver.psu_mode_type,
            sim_driver.pass_energy_type,
        ]
    elif isinstance(sim_driver, SpecsAnalyserDriverIO):
        return SpecsSequence[sim_driver.lens_mode_type, sim_driver.psu_mode_type]
    raise ValueError("class " + str(sim_driver) + " not recognised")


@pytest.fixture
def sequence(
    sim_driver: AbstractAnalyserDriverIO,
    sequence_class: type[TAbstractBaseSequence],
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
