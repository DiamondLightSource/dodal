import bluesky.plan_stubs as bps
import pytest

from dodal.devices.i24.vgonio import VerticalGoniometer
from dodal.devices.util.test_utils import patch_motor


@pytest.fixture
async def vgonio(RE):
    vgonio = VerticalGoniometer("", name="fake_vgonio")
    await vgonio.connect(mock=True)
    with patch_motor(vgonio.x), patch_motor(vgonio.yh), patch_motor(vgonio.z):
        yield vgonio


def test_vertical_gonio_device_can_be_created(vgonio: VerticalGoniometer):
    assert isinstance(vgonio, VerticalGoniometer)


async def test_vgonio_motor_move(vgonio: VerticalGoniometer, RE):
    pos = (1.0, 1.5)
    RE(bps.mv(vgonio.x, pos[0], vgonio.yh, pos[1]))  # type:ignore

    assert await vgonio.x.user_readback.get_value() == 1.0
    assert await vgonio.yh.user_readback.get_value() == 1.5
