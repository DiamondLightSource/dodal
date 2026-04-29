from pathlib import Path

import pytest
from ophyd_async.core import (
    SignalDict,
    error_if_none,
    init_devices,
)
from ophyd_async.epics.adcore import ADImageMode

from dodal.common.beamlines.beamline_utils import get_path_provider, set_path_provider
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.beamlines.i11.mythen import (
    _BIT_DEPTH,
    _DEADTIMES,
    Mythen3,
    Mythen3TriggerMode,
)


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
            writer_suffix="HDF:",
        )

    return i11_mythen


def test_mythen_deadtime(i11_mythen: Mythen3) -> None:
    # deadtime is constant for Mythen3, so we can just check it
    trigger_logic = error_if_none(
        i11_mythen._trigger_logic, "TriggerLogic cannot be None."
    )
    assert trigger_logic.get_deadtime(SignalDict()) == _DEADTIMES[_BIT_DEPTH]


async def test_mythen_prepare_when_det_trig_internal(i11_mythen: Mythen3) -> None:
    trigger_logic = error_if_none(
        i11_mythen._trigger_logic, "TriggerLogic cannot be None."
    )
    await trigger_logic.prepare_internal(num=1, livetime=10.0, deadtime=1)
    assert (
        await i11_mythen.driver.trigger_mode.get_value() == Mythen3TriggerMode.INTERNAL
    )


async def test_mythen_prepare_when_det_trig_external(i11_mythen: Mythen3) -> None:
    trigger_logic = error_if_none(
        i11_mythen._trigger_logic, "TriggerLogic cannot be None."
    )
    await trigger_logic.prepare_level(num=1)
    assert (
        await i11_mythen.driver.trigger_mode.get_value() == Mythen3TriggerMode.EXTERNAL
    )


async def test_mythen_prepare_when_continous_exposure(i11_mythen: Mythen3) -> None:
    trigger_logic = error_if_none(
        i11_mythen._trigger_logic, "TriggerLogic cannot be None."
    )
    await trigger_logic.prepare_edge(num=0, livetime=10)
    assert await i11_mythen.driver.image_mode.get_value() == ADImageMode.CONTINUOUS
