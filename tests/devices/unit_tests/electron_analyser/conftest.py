from typing import Any

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import SignalR, init_devices, soft_signal_rw

from dodal.devices.electron_analyser import (
    DualEnergySource,
    ElectronAnalyserDetector,
    SingleEnergySource,
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
from tests.devices.unit_tests.electron_analyser.helper_util import (
    get_test_sequence,
)


@pytest.fixture
def pgm_energy(RE: RunEngine) -> SignalR[float]:
    with init_devices(mock=True):
        pgm_energy = soft_signal_rw(float, initial_value=100, units="eV")
    return pgm_energy


@pytest.fixture
def dcm_energy(RE: RunEngine) -> SignalR[float]:
    with init_devices(mock=True):
        dcm_energy = soft_signal_rw(float, initial_value=2200, units="eV")
    return dcm_energy


@pytest.fixture
async def single_energy_source(
    dcm_energy: SignalR[float], RE: RunEngine
) -> SingleEnergySource:
    async with init_devices(mock=True):
        single_energy_source = SingleEnergySource(
            dcm_energy,
        )
    return single_energy_source


@pytest.fixture
async def dual_energy_source(
    dcm_energy: SignalR[float], pgm_energy: SignalR[float], RE: RunEngine
) -> DualEnergySource:
    async with init_devices(mock=True):
        dual_energy_source = DualEnergySource(dcm_energy, pgm_energy)
    return dual_energy_source


@pytest.fixture
async def energy_sources(
    dcm_energy: SignalR[float], pgm_energy: SignalR[float]
) -> dict[str, SignalR[float]]:
    return {"source1": dcm_energy, "source2": pgm_energy}


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
