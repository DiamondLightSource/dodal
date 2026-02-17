from typing import Any

import pytest
from ophyd_async.core import InOut, init_devices, set_mock_value

from dodal.devices.beamlines.b07 import B07BSpecs150
from dodal.devices.beamlines.i09 import Grating, I09VGScientaEW4000
from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorWithDSpacing,
    PitchAndRollCrystal,
    StationaryCrystal,
)
from dodal.devices.electron_analyser.base import (
    AbstractBaseRegion,
    AbstractBaseSequence,
    DualEnergySource,
    EnergySource,
    GenericElectronAnalyserDetector,
)
from dodal.devices.fast_shutter import DualFastShutter, GenericFastShutter
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.selectable_source import SourceSelector


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


def fast_shutter() -> GenericFastShutter:
    with init_devices(mock=True):
        fast_shutter = GenericFastShutter[InOut](
            pv="TEST:",
            open_state=InOut.OUT,
            close_state=InOut.IN,
        )
    return fast_shutter


@pytest.fixture
def shutter1() -> GenericFastShutter[InOut]:
    with init_devices(mock=True):
        shutter1 = GenericFastShutter[InOut](
            pv="TEST:",
            open_state=InOut.OUT,
            close_state=InOut.IN,
        )
    return shutter1


@pytest.fixture
def shutter2() -> GenericFastShutter[InOut]:
    with init_devices(mock=True):
        shutter2 = GenericFastShutter[InOut](
            pv="TEST:",
            open_state=InOut.OUT,
            close_state=InOut.IN,
        )
    return shutter2


@pytest.fixture
def dual_fast_shutter(
    shutter1: GenericFastShutter[InOut],
    shutter2: GenericFastShutter[InOut],
    source_selector: SourceSelector,
) -> DualFastShutter[InOut]:
    with init_devices(mock=True):
        dual_fast_shutter = DualFastShutter[InOut](
            shutter1,
            shutter2,
            source_selector.selected_source,
        )
    return dual_fast_shutter


@pytest.fixture
async def b07b_specs150(
    single_energy_source: EnergySource,
    shutter1: GenericFastShutter,
) -> B07BSpecs150:
    with init_devices(mock=True):
        b07b_specs150 = B07BSpecs150(
            prefix="TEST:",
            energy_source=single_energy_source,
            shutter=shutter1,
        )
    # Needed for specs so we don't get division by zero error.
    set_mock_value(b07b_specs150.driver.slices, 1)
    return b07b_specs150


@pytest.fixture
async def ew4000(
    dual_energy_source: DualEnergySource,
    dual_fast_shutter: DualFastShutter,
    source_selector: SourceSelector,
) -> I09VGScientaEW4000:
    with init_devices(mock=True):
        ew4000 = I09VGScientaEW4000(
            prefix="TEST:",
            dual_energy_source=dual_energy_source,
            dual_fast_shutter=dual_fast_shutter,
            source_selector=source_selector,
        )
    return ew4000


@pytest.fixture(params=["ew4000", "b07b_specs150"])
def sim_detector(
    request: pytest.FixtureRequest,
    ew4000: I09VGScientaEW4000,
    b07b_specs150: B07BSpecs150,
) -> GenericElectronAnalyserDetector:
    detectors = [ew4000, b07b_specs150]
    for detector in detectors:
        if detector.name == request.param:
            return detector

    raise ValueError(f"Detector with name '{request.param}' not found")


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
