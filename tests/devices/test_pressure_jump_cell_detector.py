import asyncio

import pytest
from ophyd_async.core import (
    DetectorTrigger,
    PathProvider,
    TriggerInfo,
    callback_on_mock_put,
    init_devices,
    set_mock_value,
)

from dodal.devices.areadetector import PressureJumpCellDetector
from dodal.devices.areadetector.pressurejumpcell_io import (
    AdcTriggerMode,
    AdcTriggerState,
    PressureJumpCellTriggerMode,
)


@pytest.fixture
async def cell_ad(static_path_provider: PathProvider) -> PressureJumpCellDetector:
    async with init_devices(mock=True):
        pjump_ad = PressureJumpCellDetector("DEMO-PJUMPAD-01:", static_path_provider)

    return pjump_ad


@pytest.fixture
async def cell_ad_with_mocked_arm(
    cell_ad: PressureJumpCellDetector,
) -> PressureJumpCellDetector:
    async def set_acquire(value, *_, **__):
        async def value_set():
            await asyncio.sleep(0)
            set_mock_value(cell_ad.driver.acquire, value)

        asyncio.create_task(value_set())

    async def set_state(value, *_, **__):
        async def value_set_state_armed():
            await asyncio.sleep(0)
            set_mock_value(cell_ad.trig.capture, value)
            if value:
                await asyncio.sleep(0)
                set_mock_value(
                    cell_ad.trig.state, AdcTriggerState.ARMED
                )  # prepare capture
                set_mock_value(cell_ad.driver.acquire, True)
                await asyncio.sleep(0)
                set_mock_value(cell_ad.trig.state, AdcTriggerState.IDLE)  # end capture

        asyncio.create_task(value_set_state_armed())

    callback_on_mock_put(cell_ad.driver.acquire, set_acquire)
    callback_on_mock_put(cell_ad.trig.capture, set_state)

    return cell_ad


async def test_pjumpcellad_driver_includes_trigger_mode(
    cell_ad: PressureJumpCellDetector,
):
    set_mock_value(cell_ad.driver.trigger_mode, PressureJumpCellTriggerMode.EXTERNAL)

    await cell_ad.driver.trigger_mode.set(PressureJumpCellTriggerMode.INTERNAL)

    assert (
        await cell_ad.driver.trigger_mode.get_value()
        == PressureJumpCellTriggerMode.INTERNAL
    )


async def test_pjumpcellad_trigger_includes_capture(
    cell_ad: PressureJumpCellDetector,
):
    set_mock_value(cell_ad.trig.capture, False)

    await cell_ad.trig.capture.set(True)

    assert await cell_ad.trig.capture.get_value()


async def test_pjumpcellad_trigger_includes_triggermode(
    cell_ad: PressureJumpCellDetector,
):
    set_mock_value(cell_ad.trig.trigger_mode, AdcTriggerMode.CONTINUOUS)

    await cell_ad.trig.trigger_mode.set(AdcTriggerMode.SINGLE)

    assert await cell_ad.trig.trigger_mode.get_value() == AdcTriggerMode.SINGLE


async def test_pjumpcellad_controller(
    cell_ad_with_mocked_arm: PressureJumpCellDetector,
):
    cell_ad_ctrl = cell_ad_with_mocked_arm._controller

    await cell_ad_ctrl.prepare(TriggerInfo(trigger=DetectorTrigger.INTERNAL))

    await cell_ad_ctrl.arm()

    await cell_ad_ctrl.wait_for_idle()


async def test_pjumpcellad_disarm_sets_capture(
    cell_ad_with_mocked_arm: PressureJumpCellDetector,
):
    cell_ad_ctrl = cell_ad_with_mocked_arm._controller

    await cell_ad_ctrl.prepare(TriggerInfo(trigger=DetectorTrigger.INTERNAL))

    await cell_ad_ctrl.arm()

    await cell_ad_ctrl.disarm()

    assert not await cell_ad_ctrl.trig.capture.get_value()


async def test_pjumpcellad_disarm_sets_driver_acquire(
    cell_ad_with_mocked_arm: PressureJumpCellDetector,
):
    cell_ad_ctrl = cell_ad_with_mocked_arm._controller

    await cell_ad_ctrl.prepare(TriggerInfo(trigger=DetectorTrigger.INTERNAL))

    await cell_ad_ctrl.arm()

    await cell_ad_ctrl.disarm()

    assert not await cell_ad_ctrl.driver.acquire.get_value()


async def test_pjumpcellad_setting_trigger_info_livetime_sets_acquire_time(
    cell_ad_with_mocked_arm: PressureJumpCellDetector,
):
    cell_ad_ctrl = cell_ad_with_mocked_arm._controller

    livetime_value = 123

    await cell_ad_ctrl.prepare(
        TriggerInfo(trigger=DetectorTrigger.INTERNAL, livetime=livetime_value)
    )

    assert await cell_ad_ctrl.driver.acquire_time.get_value() == livetime_value
