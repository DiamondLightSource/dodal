from unittest.mock import MagicMock

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine

from dodal.devices.i24.pmac import HOME_STR, PMAC

from ..conftest import patch_motor


@pytest.fixture
async def fake_pmac_and_log():
    call_log = MagicMock()

    RunEngine()
    pmac = PMAC("", name="fake_pmac")
    await pmac.connect(mock=True)

    with (
        patch_motor(pmac.x, call_log=call_log),
        patch_motor(pmac.y, call_log=call_log),
        patch_motor(pmac.z, call_log=call_log),
    ):
        yield pmac, call_log


@pytest.fixture
async def fake_pmac(fake_pmac_and_log) -> PMAC:
    fake_pmac, _ = fake_pmac_and_log
    return fake_pmac


def test_pmac_can_be_created(fake_pmac: PMAC):
    assert isinstance(fake_pmac, PMAC)


async def test_pmac_motor_move(fake_pmac: PMAC, RE):
    pos = (1.0, 0.5)
    RE(bps.mv(fake_pmac.x, pos[0], fake_pmac.y, pos[1]))

    assert await fake_pmac.x.user_readback.get_value() == 1.0
    assert await fake_pmac.y.user_readback.get_value() == 0.5


async def test_pmac_set_pmac_string(fake_pmac: PMAC, RE):
    RE(bps.abs_set(fake_pmac.pmac_string, "!x0y0z0", wait=True))

    assert await fake_pmac.pmac_string.get_value() == "!x0y0z0"


async def test_pmac_home(fake_pmac: PMAC, RE):
    RE(bps.trigger(fake_pmac.home, wait=True))

    assert await fake_pmac.pmac_string.get_value() == HOME_STR
