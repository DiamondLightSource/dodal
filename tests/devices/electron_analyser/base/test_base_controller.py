from unittest.mock import AsyncMock, patch

import pytest
from ophyd_async.core import TriggerInfo, get_mock_put, init_devices

from dodal.devices.b07.analyser import Specs2DCMOS
from dodal.devices.electron_analyser.base import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    DualEnergySource,
    EnergySource,
)
from dodal.devices.electron_analyser.base.base_controller import (
    ElectronAnalyserController,
)
from dodal.devices.fast_shutter import DualFastShutter
from dodal.devices.i09.analyser import EW4000
from dodal.devices.selectable_source import SourceSelector
from tests.devices.electron_analyser.helper_util import TEST_SEQUENCE_REGION_NAMES


@pytest.fixture
def ew4000(
    dual_energy_source: DualEnergySource,
    dual_fast_shutter: DualFastShutter,
    source_selector: SourceSelector,
) -> EW4000:
    with init_devices(mock=True):
        ew4000 = EW4000("TEST:", dual_energy_source, dual_fast_shutter, source_selector)
    return ew4000


@pytest.fixture
def specs_2dcmos(single_energy_source: EnergySource) -> Specs2DCMOS:
    with init_devices(mock=True):
        specs_2dcmos = Specs2DCMOS("TEST:", single_energy_source)
    return specs_2dcmos


@pytest.fixture(params=["ew4000", "specs_2dcmos"])
def analyser_controller(
    request: pytest.FixtureRequest, ew4000: EW4000, specs_2dcmos: Specs2DCMOS
):
    detectors = [ew4000, specs_2dcmos]
    for detector in detectors:
        if detector.name == request.param:
            return detector._controller

    raise ValueError(f"Detector with name '{request.param}' not found")


@pytest.fixture
def sim_driver(
    analyser_controller: ElectronAnalyserController[
        AbstractAnalyserDriverIO, AbstractBaseRegion
    ],
) -> AbstractAnalyserDriverIO:
    return analyser_controller.driver


async def test_controller_prepare_sets_excitation_energy(
    analyser_controller: ElectronAnalyserController[
        AbstractAnalyserDriverIO, AbstractBaseRegion
    ],
) -> None:
    excitation_energy = await analyser_controller.energy_source.energy.get_value()
    await analyser_controller.prepare(TriggerInfo())
    get_mock_put(
        analyser_controller.driver.cached_excitation_energy
    ).assert_awaited_once_with(excitation_energy, wait=True)


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_controller_setup_with_region_sets_region_for_epics_and_sets_driver(
    analyser_controller: ElectronAnalyserController[
        AbstractAnalyserDriverIO, AbstractBaseRegion
    ],
    region: AbstractBaseRegion,
) -> None:
    sim_driver = analyser_controller.driver
    sim_driver.set = AsyncMock()

    # Patch switch_energy_mode so we can check on calls, but still run the real function
    with patch.object(
        AbstractBaseRegion,
        "prepare_for_epics",
        side_effect=AbstractBaseRegion.prepare_for_epics,  # run the real method
        autospec=True,
    ) as mock_prepare_for_epics:
        await analyser_controller.setup_with_region(region)

        mock_prepare_for_epics.assert_called_once_with(
            region,
            await analyser_controller.energy_source.energy.get_value(),
        )

        source_selector = analyser_controller.source_selector
        if source_selector is not None:
            get_mock_put(source_selector.selected_source).assert_called_once_with(
                region.excitation_energy_source, wait=True
            )
        # Check set was called with epics_region
        epics_region = mock_prepare_for_epics.call_args[0][0].prepare_for_epics(
            await analyser_controller.energy_source.energy.get_value(),
        )
        sim_driver.set.assert_called_once_with(epics_region)


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_controller_setup_with_region_moves_selected_source_if_not_none(
    analyser_controller: ElectronAnalyserController[
        AbstractAnalyserDriverIO, AbstractBaseRegion
    ],
    region: AbstractBaseRegion,
) -> None:
    source_selector = analyser_controller.source_selector

    if source_selector is not None:
        await analyser_controller.setup_with_region(region)
        get_mock_put(source_selector.selected_source).assert_awaited_once_with(
            region.excitation_energy_source, wait=True
        )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_controller_setup_with_region_moves_shutter_if_not_none(
    analyser_controller: ElectronAnalyserController[
        AbstractAnalyserDriverIO, AbstractBaseRegion
    ],
    region: AbstractBaseRegion,
) -> None:
    shutter = analyser_controller.shutter
    if shutter is not None:
        await analyser_controller.setup_with_region(region)
        get_mock_put(shutter.shutter_state).assert_awaited_once_with(
            shutter.close_state, wait=True
        )


async def test_controller_prepare_moves_shutters_if_not_none(
    analyser_controller: ElectronAnalyserController[
        AbstractAnalyserDriverIO, AbstractBaseRegion
    ],
) -> None:
    shutter = analyser_controller.shutter
    if shutter is not None:
        await analyser_controller.prepare(TriggerInfo())
        get_mock_put(shutter.shutter_state).assert_awaited_once_with(
            shutter.open_state, wait=True
        )
