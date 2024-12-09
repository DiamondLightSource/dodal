import asyncio
from unittest.mock import call, patch

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.testing import callback_on_mock_put, get_mock_put, set_mock_value

from dodal.devices.i24.pmac import (
    HOME_STR,
    PMAC,
    EncReset,
    LaserSettings,
)
from dodal.devices.util.test_utils import patch_motor


@pytest.fixture
async def fake_pmac():
    RunEngine()
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
    RE(bps.mv(fake_pmac.x, pos[0], fake_pmac.y, pos[1]))  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827

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
    set_mock_value(fake_pmac.collection_time, 2.0)
    await fake_pmac.run_program.kickoff()
    await fake_pmac.run_program.complete()

    assert await fake_pmac.pmac_string.get_value() == "&2b11r"


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
