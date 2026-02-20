from unittest.mock import AsyncMock, patch

import pytest
from ophyd_async.core import TriggerInfo, get_mock_put

from dodal.devices.electron_analyser.base import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    ElectronAnalyserController,
    GenericElectronAnalyserController,
    GenericElectronAnalyserDetector,
    GenericSequence,
)
from tests.devices.electron_analyser.helper_util import (
    TEST_SEQUENCE_REGION_NAMES,
    get_test_sequence,
)


@pytest.fixture
def sequence(sim_detector: GenericElectronAnalyserDetector) -> GenericSequence:
    return get_test_sequence(type(sim_detector))


@pytest.fixture
def analyser_controller(
    sim_detector: GenericElectronAnalyserDetector,
) -> GenericElectronAnalyserController:
    return sim_detector._controller


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
