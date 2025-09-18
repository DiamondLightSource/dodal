import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_reading,
    get_mock_put,
    partial_reading,
    set_mock_value,
)

from dodal.devices.turbo_slit import TurboSlit
from dodal.testing.setup import patch_all_motors


@pytest.fixture
def slit() -> TurboSlit:
    with init_devices(mock=True):
        slit = TurboSlit(prefix="TEST-EA-TURBOSLIT:", name="turbo_slit")
    with patch_all_motors(slit):
        return slit


async def test_turbo_slit_set(slit: TurboSlit):
    await slit.set(0.5)

    assert get_mock_put(slit.xfine.user_setpoint).call_count == 1
    get_mock_put(slit.xfine.user_setpoint).assert_called_once_with(0.5, wait=True)


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
