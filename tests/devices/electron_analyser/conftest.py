from typing import Any

import numpy as np
import pytest
from ophyd_async.core import (
    SignalR,
    SignalRW,
    init_devices,
    set_mock_value,
    soft_signal_rw,
)
from ophyd_async.epics.adcore import ADAcquireLogic

from dodal.devices.beamlines import b07, b07_shared, i05_shared, i09
from dodal.devices.beamlines.i09 import Grating
from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorWithDSpacing,
    PitchAndRollCrystal,
    StationaryCrystal,
)
from dodal.devices.electron_analyser.base import (
    DualEnergySource,
    ElectronAnalyserTriggerLogic,
    RegionLogic,
)
from dodal.devices.electron_analyser.mbs import MbsAnalyserDriverIO, MbsDetector
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO, SpecsDetector
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaDetector,
)
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.selectable_source import SelectedSource


@pytest.fixture
async def source_selector() -> SignalRW[SelectedSource]:
    async with init_devices(mock=True):
        source_selector = soft_signal_rw(SelectedSource)
    return source_selector


@pytest.fixture
async def source_energy() -> SignalR[float]:
    async with init_devices(mock=True):
        dcm = DoubleCrystalMonochromatorWithDSpacing(
            "DCM:", PitchAndRollCrystal, StationaryCrystal
        )
    await dcm.energy_in_keV.set(2.2)
    return dcm.energy_in_eV


@pytest.fixture
async def dual_energy_source(
    source_selector: SignalRW[SelectedSource],
) -> DualEnergySource:
    async with init_devices(mock=True):
        dcm = DoubleCrystalMonochromatorWithDSpacing(
            "DCM:", PitchAndRollCrystal, StationaryCrystal
        )
        pgm = PlaneGratingMonochromator("PGM:", Grating)
        await dcm.energy_in_keV.set(2.2)
        await pgm.energy.set(500)
        dual_energy_source = DualEnergySource(
            source1=dcm.energy_in_eV,
            source2=pgm.energy.user_readback,
            selected_source=source_selector,
        )
    return dual_energy_source


@pytest.fixture
async def dual_source_energy(dual_energy_source: DualEnergySource) -> SignalR[float]:
    return dual_energy_source.energy


@pytest.fixture
async def b07b_specs150(
    source_energy: SignalR[float],
) -> SpecsDetector[b07.LensMode, b07_shared.PsuMode]:
    with init_devices(mock=True):
        prefix = "TEST:"
        driver = SpecsAnalyserDriverIO(prefix, b07.LensMode, b07_shared.PsuMode)
        b07b_specs150 = SpecsDetector[b07.LensMode, b07_shared.PsuMode](
            prefix,
            driver,
            acquire_logic=ADAcquireLogic(driver),
            trigger_logic=ElectronAnalyserTriggerLogic(driver),
            region_logic=RegionLogic(driver, source_energy),
        )
    # Needed for specs so we don't get division by zero error.
    set_mock_value(b07b_specs150.driver.slices, 1)
    return b07b_specs150


@pytest.fixture
async def ew4000(
    dual_energy_source: DualEnergySource,
    source_selector: SignalRW[SelectedSource],
) -> VGScientaDetector[i09.LensMode, i09.PsuMode, i09.PassEnergy]:
    with init_devices(mock=True):
        prefix = "TEST:"
        driver = VGScientaAnalyserDriverIO(
            prefix, i09.LensMode, i09.PsuMode, i09.PassEnergy
        )
        ew4000 = VGScientaDetector[i09.LensMode, i09.PsuMode, i09.PassEnergy](
            prefix,
            driver,
            acquire_logic=ADAcquireLogic(driver),
            trigger_logic=ElectronAnalyserTriggerLogic(driver),
            region_logic=RegionLogic(
                driver, dual_energy_source.energy, source_selector
            ),
        )
    energy_axis = [1, 2, 3, 4, 5]
    set_mock_value(ew4000.driver.energy_axis, np.array(energy_axis, dtype=float))
    return ew4000


@pytest.fixture
async def i05_mbs_analyser(
    source_energy: SignalR[float],
) -> MbsDetector[i05_shared.LensMode, i05_shared.PassEnergy]:
    with init_devices(mock=True):
        prefix = "TEST:"
        driver = MbsAnalyserDriverIO(prefix, i05_shared.LensMode, i05_shared.PassEnergy)
        i05_mbs_analyser = MbsDetector[i05_shared.LensMode, i05_shared.PassEnergy](
            prefix,
            driver,
            acquire_logic=ADAcquireLogic(driver),
            trigger_logic=ElectronAnalyserTriggerLogic(driver),
            region_logic=RegionLogic(driver, source_energy),
        )
    energy_axis = [1, 2, 3, 4, 5]
    set_mock_value(
        i05_mbs_analyser.driver.energy_axis, np.array(energy_axis, dtype=float)
    )
    return i05_mbs_analyser


@pytest.fixture
def expected_enabled_region_names(
    expected_region_values: list[dict[str, Any]],
) -> list[str]:
    names = []
    for expected_region_value in expected_region_values:
        if expected_region_value["enabled"]:
            names.append(expected_region_value["name"])
    return names
