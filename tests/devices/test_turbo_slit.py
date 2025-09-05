from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading, set_mock_value

from dodal.devices.turbo_slit import TurboSlit


@pytest.fixture
def slit() -> TurboSlit:
    with init_devices(mock=True):
        slit = TurboSlit(prefix="TEST-EA-TURBOSLIT:", name="turbo_slit")
    return slit


async def test_turbo_slit_set(slit: TurboSlit):
    slit.xfine.set = AsyncMock()

    set_mock_value(slit.xfine.user_readback, 0.0)
    # NOTE velocity needs to be set otherwise it's zero
    # and the set method throws divide by zero error
    set_mock_value(slit.xfine.velocity, 0.2)
    await slit.set(0.5)

    assert slit.xfine.set.call_count == 1
    slit.xfine.set.assert_called_once_with(0.5)


async def test_turbo_slit_read(slit: TurboSlit):
    set_mock_value(slit.gap.user_readback, 0.5)
    set_mock_value(slit.arc.user_readback, 1.0)
    set_mock_value(slit.xfine.user_readback, 1.5)

    await assert_reading(
        slit,
        {
            "turbo_slit-gap": partial_reading(0.5),
            "turbo_slit-arc": partial_reading(1.0),
            "turbo_slit-xfine": partial_reading(1.5),
        },
    )
