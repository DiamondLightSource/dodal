from unittest.mock import AsyncMock, patch

import pytest
from ophyd_async.core import InOut, TriggerInfo, get_mock_put, init_devices

from dodal.beamlines import b07, i09
from dodal.devices.electron_analyser.base import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    DualEnergySource,
    EnergySource,
)
from dodal.devices.electron_analyser.base.base_controller import (
    ElectronAnalyserController,
)
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.fast_shutter import DualFastShutter, GenericFastShutter
from dodal.devices.selectable_source import SourceSelector
from dodal.testing.electron_analyser import create_driver
from tests.devices.electron_analyser.helper_util import (
    TEST_SEQUENCE_REGION_NAMES,
    get_test_sequence,
)


@pytest.fixture(
    params=[
        SpecsAnalyserDriverIO[b07.LensMode, b07.PsuMode],
        VGScientaAnalyserDriverIO[i09.LensMode, i09.PsuMode, i09.PassEnergy],
    ]
)
async def sim_driver(
    request: pytest.FixtureRequest,
) -> AbstractAnalyserDriverIO:
    async with init_devices(mock=True):
        sim_detector = create_driver(
            request.param,
            prefix="TEST:",
        )
    return sim_detector


@pytest.fixture
def sequence_file_path(
    sim_driver: AbstractAnalyserDriverIO,
) -> str:
    return get_test_sequence(type(sim_driver))


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
def analyser_controller(
    sim_driver: AbstractAnalyserDriverIO,
    single_energy_source: EnergySource,
    dual_energy_source: DualEnergySource,
    dual_fast_shutter: DualFastShutter,
    source_selector: SourceSelector,
) -> ElectronAnalyserController[AbstractAnalyserDriverIO, AbstractBaseRegion]:
    if isinstance(sim_driver, SpecsAnalyserDriverIO):
        controller = ElectronAnalyserController[
            AbstractAnalyserDriverIO, AbstractBaseRegion
        ](
            sim_driver,
            single_energy_source,
            source_selector=None,
        )
    elif isinstance(sim_driver, VGScientaAnalyserDriverIO):
        controller = ElectronAnalyserController[
            AbstractAnalyserDriverIO, AbstractBaseRegion
        ](
            sim_driver,
            dual_energy_source,
            dual_fast_shutter,
            source_selector,
        )
    else:
        raise ValueError(f"sim_driver is of unsupported type {type(sim_driver)}.")

    return controller


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
