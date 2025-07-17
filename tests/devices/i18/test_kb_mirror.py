import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading, set_mock_value

from dodal.devices.i18.KBMirror import KBMirror


@pytest.fixture
async def kbmirror() -> KBMirror:
    """Fixture to set up a mock KBMirror device using init_devices."""
    async with init_devices(mock=True):
        kbmirror = KBMirror(prefix="MIRROR:")
    return kbmirror


async def test_setting_xy_position_kbmirror(kbmirror: KBMirror):
    """
    Test setting x and y positions on the KBMirror using the ophyd_async mock tools.
    """
    # Mock the initial values of the x and y signals
    set_mock_value(kbmirror.x, 0.0)
    set_mock_value(kbmirror.y, 0.0)

    # Call set to update the position
    await kbmirror.x.set(1.23)
    await kbmirror.y.set(4.56)

    await assert_reading(
        kbmirror,
        {
            "kbmirror-y": partial_reading(4.56),
            "kbmirror-bend1": partial_reading(0.0),
            "kbmirror-ellip": partial_reading(0.0),
            "kbmirror-x": partial_reading(1.23),
            "kbmirror-bend2": partial_reading(0.0),
            "kbmirror-curve": partial_reading(0.0),
        },
    )
