import pytest
from ophyd_async.core import DetectorTrigger, TriggerInfo
from ophyd_async.epics.adcore import ADImageMode

from dodal.beamlines import i11
from dodal.devices.beamlines.i11.mythen import (
    _BIT_DEPTH,
    _DEADTIMES,
    Mythen3,
    Mythen3TriggerMode,
)


@pytest.fixture
async def i11_mythen() -> Mythen3:
    return i11.mythen3.build(connect_immediately=True, mock=True)


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
