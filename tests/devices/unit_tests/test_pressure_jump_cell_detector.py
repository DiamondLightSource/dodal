import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import PathProvider, init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.areadetector import PressureJumpCellDetector
from dodal.devices.areadetector.pressurejumpcell_io import (
    AdcTriggerMode,
    PressureJumpCellTriggerMode,
)


@pytest.fixture
async def cell_ad(
    static_path_provider: PathProvider, RE: RunEngine
) -> PressureJumpCellDetector:
    async with init_devices(mock=True):
        pjump_ad = PressureJumpCellDetector("DEMO-PJUMPAD-01:", static_path_provider)

    return pjump_ad


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
