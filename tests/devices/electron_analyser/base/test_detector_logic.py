from collections.abc import Callable
from typing import Any
from unittest.mock import ANY, AsyncMock, call, patch

import pytest
from ophyd_async.core import (
    SignalDict,
    StandardDetector,
    get_mock_put,
    init_devices,
    soft_signal_rw,
)
from ophyd_async.epics.adcore import ADImageMode
from ophyd_async.testing import assert_configuration, partial_reading

from dodal.devices.beamlines import b07, b07_shared, i09
from dodal.devices.electron_analyser.base import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    AbstractBaseSequence,
    AbstractEnergySource,
)
from dodal.devices.electron_analyser.base.detector_logic import (
    ElectronAnalayserTriggerLogic,
    RegionLogic,
    ShutterCoordinatorADArmLogic,
)
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.vgscienta import VGScientaAnalyserDriverIO
from dodal.devices.fast_shutter import GenericFastShutter
from dodal.devices.selectable_source import SourceSelector
from tests.devices.electron_analyser.helper_util import (
    TEST_SEQUENCE_REGION_NAMES,
    get_test_sequence,
)


@pytest.fixture
def vgscienta_driver() -> VGScientaAnalyserDriverIO:
    with init_devices(mock=True):
        vgscienta_driver = VGScientaAnalyserDriverIO(
            "TEST:", i09.LensMode, i09.PsuMode, i09.PassEnergy
        )
    return vgscienta_driver


@pytest.fixture
def specs_driver() -> SpecsAnalyserDriverIO:
    with init_devices(mock=True):
        specs_driver = SpecsAnalyserDriverIO("TEST:", b07.LensMode, b07_shared.PsuMode)
    return specs_driver


@pytest.fixture(params=["specs_driver", "vgscienta_driver"])
def driver(request: pytest.FixtureRequest) -> AbstractAnalyserDriverIO:
    return request.getfixturevalue(request.param)


@pytest.fixture(params=["shutter1", "dual_fast_shutter"])
def shutter(request: pytest.FixtureRequest) -> GenericFastShutter:
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize(
    "close_shutter_idle, expected_shutter_calls",
    [
        (True, lambda s: [call(s.open_state), call(s.close_state)]),
        (False, lambda s: [call(s.open_state)]),
    ],
)
async def test_shutter_arm_logic_opens_shutters(
    driver: AbstractAnalyserDriverIO,
    shutter: GenericFastShutter,
    close_shutter_idle: bool,
    expected_shutter_calls: Callable[[GenericFastShutter], list[Any]],
):
    with init_devices(mock=True):
        close_shutter_idle_signal = soft_signal_rw(bool, close_shutter_idle)

    shutter_arm_logic = ShutterCoordinatorADArmLogic(
        driver, shutter, close_shutter_idle_signal
    )

    detector = StandardDetector()
    detector.add_detector_logics(shutter_arm_logic)

    await detector.stage()
    await detector.trigger()
    await detector.unstage()

    # Test driver acquire expected number of times.
    get_mock_put(driver.acquire).assert_has_awaits(
        [call(False), call(True), call(False)]
    )

    # Test expected shutter calls.
    shutter = shutter_arm_logic._shutter
    get_mock_put(shutter.shutter_state).assert_has_awaits(
        expected_shutter_calls(shutter)
    )


@pytest.fixture(params=["single_energy_source", "dual_energy_source"])
def energy_source(request: pytest.FixtureRequest) -> AbstractEnergySource:
    return request.getfixturevalue(request.param)


@pytest.fixture
def sequence(driver: AbstractAnalyserDriverIO) -> AbstractBaseSequence:
    return get_test_sequence(type(driver))


@pytest.fixture
def region_logic(
    driver: AbstractAnalyserDriverIO,
    energy_source: AbstractEnergySource,
    source_selector: SourceSelector,
) -> RegionLogic:
    return RegionLogic(driver, energy_source, source_selector)


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_region_logic_setup_with_region_sets_region_for_epics_and_sets_driver(
    region: AbstractBaseRegion,
    region_logic: RegionLogic,
) -> None:

    region_logic.driver.set = AsyncMock()

    # Patch switch_energy_mode so we can check on calls, but still run the real function
    with patch.object(
        AbstractBaseRegion,
        "prepare_for_epics",
        side_effect=AbstractBaseRegion.prepare_for_epics,  # run the real method
        autospec=True,
    ) as mock_prepare_for_epics:
        await region_logic.setup_with_region(region)

        mock_prepare_for_epics.assert_called_once_with(
            region,
            await region_logic.energy_source.energy.get_value(),
        )

        if region_logic.source_selector is not None:
            get_mock_put(
                region_logic.source_selector.selected_source
            ).assert_called_once_with(region.excitation_energy_source)
        # Check set was called with epics_region
        epics_region = mock_prepare_for_epics.call_args[0][0].prepare_for_epics(
            await region_logic.energy_source.energy.get_value(),
        )
        region_logic.driver.set.assert_called_once_with(epics_region)


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_region_logic_setup_with_region_moves_selected_source_if_not_none(
    region: AbstractBaseRegion, region_logic: RegionLogic
) -> None:

    if region_logic.source_selector is not None:
        await region_logic.setup_with_region(region)
        get_mock_put(
            region_logic.source_selector.selected_source
        ).assert_awaited_once_with(region.excitation_energy_source)


@pytest.fixture
def trigger_logic(driver: AbstractAnalyserDriverIO) -> ElectronAnalayserTriggerLogic:
    return ElectronAnalayserTriggerLogic(driver, {driver.lens_mode, driver.psu_mode})


async def test_electron_analyser_trigger_logic_prepare_internal(
    trigger_logic: ElectronAnalayserTriggerLogic,
) -> None:
    detector = StandardDetector()
    detector.add_detector_logics(trigger_logic)
    await detector.trigger()
    get_mock_put(trigger_logic.driver.image_mode).assert_awaited_once_with(
        ADImageMode.SINGLE
    )


async def test_electron_analyser_trigger_logic_config_sigs(
    trigger_logic: ElectronAnalayserTriggerLogic,
) -> None:
    detector = StandardDetector()
    detector.add_detector_logics(trigger_logic)

    await assert_configuration(
        detector,
        {
            trigger_logic.driver.lens_mode.name: partial_reading(ANY),
            trigger_logic.driver.psu_mode.name: partial_reading(ANY),
        },
    )


async def test_electron_analyser_deadtime(
    trigger_logic: ElectronAnalayserTriggerLogic,
) -> None:
    assert trigger_logic.get_deadtime(SignalDict()) == 0.0
