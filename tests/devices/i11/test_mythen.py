from pathlib import Path

import pytest
from ophyd_async.core import DetectorTrigger, TriggerInfo, init_devices
from ophyd_async.epics.adcore import ADImageMode

# from ophyd_async.testing import set_mock_value
from dodal.common.beamlines.beamline_utils import get_path_provider, set_path_provider
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.i11.mythen import _BIT_DEPTH, _DEADTIMES, Mythen3, Mythen3TriggerMode


@pytest.fixture
async def i11_mythen() -> Mythen3:
    set_path_provider(
        StaticVisitPathProvider(
            "i11",
            Path("/dls/i11/data/2025/cm12356-1/"),
            client=LocalDirectoryServiceClient(),
        )
    )

    async with init_devices(mock=True):
        i11_mythen = Mythen3(
            prefix="BL11I-EA-DET-07:",
            path_provider=get_path_provider(),
            drv_suffix="DET",
            fileio_suffix="HDF:",
        )

    return i11_mythen


def test_mythen_deadtime(i11_mythen: Mythen3) -> None:
    # deadtime is constant for Mythen3, so we can just check it
    assert i11_mythen.controller.get_deadtime(10.0) == _DEADTIMES[_BIT_DEPTH]


async def test_mythen_prepare_when_det_trig_internal(i11_mythen: Mythen3) -> None:
    trigger_info = TriggerInfo(
        number_of_events=1,
        trigger=DetectorTrigger.INTERNAL,
        deadtime=1,
        livetime=10.0,
        exposure_timeout=30.0,
        exposures_per_event=1,
    )

    await i11_mythen.controller.prepare(trigger_info)
    assert (
        await i11_mythen.driver.trigger_mode.get_value() == Mythen3TriggerMode.INTERNAL
    )


async def test_mythen_prepare_when_det_trig_external(i11_mythen: Mythen3) -> None:
    trigger_info = TriggerInfo(
        number_of_events=1,
        trigger=DetectorTrigger.CONSTANT_GATE,
        deadtime=1,
        livetime=10.0,
        exposure_timeout=30.0,
        exposures_per_event=1,
    )

    await i11_mythen.controller.prepare(trigger_info)
    assert (
        await i11_mythen.driver.trigger_mode.get_value() == Mythen3TriggerMode.EXTERNAL
    )


async def test_mythen_prepare_when_continous_exposure(i11_mythen: Mythen3) -> None:
    trigger_info = TriggerInfo(
        number_of_events=0,
        trigger=DetectorTrigger.CONSTANT_GATE,
        deadtime=1,
        livetime=10.0,
        exposure_timeout=30.0,
        exposures_per_event=1,
    )

    await i11_mythen.controller.prepare(trigger_info)
    assert await i11_mythen.driver.image_mode.get_value() == ADImageMode.CONTINUOUS
