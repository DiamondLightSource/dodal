import asyncio
from unittest.mock import call, patch

import bluesky.plan_stubs as bps
import pytest
from ophyd_async.testing import callback_on_mock_put, get_mock_put, set_mock_value

from dodal.devices.i24.pmac import (
    HOME_STR,
    PMAC,
    EncReset,
    LaserSettings,
)
from dodal.devices.util.test_utils import patch_motor


@pytest.fixture
async def fake_pmac(RE):
    pmac = PMAC("", name="fake_pmac")
    await pmac.connect(mock=True)

    with (
        patch_motor(pmac.x),
        patch_motor(pmac.y),
        patch_motor(pmac.z),
    ):
        yield pmac


def test_pmac_can_be_created(fake_pmac: PMAC):
    assert isinstance(fake_pmac, PMAC)


async def test_pmac_motor_move(fake_pmac: PMAC, RE):
    pos = (1.0, 0.5)
    RE(bps.mv(fake_pmac.x, pos[0], fake_pmac.y, pos[1]))

    assert await fake_pmac.x.user_readback.get_value() == 1.0
    assert await fake_pmac.y.user_readback.get_value() == 0.5


async def test_pmac_set_pmac_string(fake_pmac: PMAC, RE):
    RE(bps.abs_set(fake_pmac.pmac_string, "M712=0 M711=1", wait=True))

    assert await fake_pmac.pmac_string.get_value() == "M712=0 M711=1"


async def test_pmac_pmac_to_zero(fake_pmac: PMAC, RE):
    RE(bps.trigger(fake_pmac.to_xyz_zero, wait=True))

    assert await fake_pmac.pmac_string.get_value() == "!x0y0z0"


async def test_pmac_home(fake_pmac: PMAC, RE):
    RE(bps.trigger(fake_pmac.home, wait=True))

    assert await fake_pmac.pmac_string.get_value() == HOME_STR


async def test_set_pmac_string_for_laser(fake_pmac: PMAC, RE):
    RE(bps.abs_set(fake_pmac.laser, LaserSettings.LASER_1_ON))

    assert await fake_pmac.pmac_string.get_value() == " M712=1 M711=1"


async def test_set_pmac_string_for_enc_reset(fake_pmac: PMAC, RE):
    RE(bps.abs_set(fake_pmac.enc_reset, EncReset.ENC7, wait=True))

    assert await fake_pmac.pmac_string.get_value() == "m708=100 m709=150"


async def test_run_program(fake_pmac: PMAC, RE):
    async def go_high_then_low():
        set_mock_value(fake_pmac.scanstatus, 1)
        await asyncio.sleep(0.01)
        set_mock_value(fake_pmac.scanstatus, 0)

    callback_on_mock_put(
        fake_pmac.pmac_string,
        lambda *args, **kwargs: asyncio.create_task(go_high_then_low()),  # type: ignore
    )

    set_mock_value(fake_pmac.program_number, 11)
    await fake_pmac.run_program.kickoff()
    await fake_pmac.run_program.complete()

    assert await fake_pmac.pmac_string.get_value() == "&2b11r"


async def update_counter(sleep_time: float, fake_pmac: PMAC):
    set_mock_value(fake_pmac.scanstatus, 1)
    set_mock_value(fake_pmac.counter, 0)
    await asyncio.sleep(0.05)
    set_mock_value(fake_pmac.counter, 1)
    await asyncio.sleep(0.05)
    set_mock_value(fake_pmac.counter, 2)
    await asyncio.sleep(sleep_time)
    set_mock_value(fake_pmac.counter, 3)
    set_mock_value(fake_pmac.scanstatus, 0)


async def test_counter_refresh(fake_pmac: PMAC, RE):
    callback_on_mock_put(
        fake_pmac.pmac_string,
        lambda *args, **kwargs: asyncio.create_task(update_counter(0.05, fake_pmac)),  # type: ignore
    )

    set_mock_value(fake_pmac.counter_time, 0.1)
    await fake_pmac.run_program.kickoff()
    await fake_pmac.run_program.complete()

    assert await fake_pmac.counter.get_value() == 3


async def test_counter_refresh_timeout(fake_pmac: PMAC, RE):
    callback_on_mock_put(
        fake_pmac.pmac_string,
        lambda *args, **kwargs: asyncio.create_task(update_counter(0.2, fake_pmac)),  # type: ignore
    )

    set_mock_value(fake_pmac.counter_time, 0.1)
    with pytest.raises(asyncio.exceptions.TimeoutError):
        await fake_pmac.run_program.kickoff()
        await fake_pmac.run_program.complete()

    assert await fake_pmac.counter.get_value() == 2


@patch("dodal.devices.i24.pmac.sleep")
async def test_abort_program(mock_sleep, fake_pmac: PMAC, RE):
    set_mock_value(fake_pmac.scanstatus, 0)
    RE(bps.trigger(fake_pmac.abort_program, wait=True))

    mock_pmac_string = get_mock_put(fake_pmac.pmac_string)
    mock_pmac_string.assert_has_calls(
        [
            call("A", wait=True),
            call("P2401=0", wait=True),
        ]
    )
