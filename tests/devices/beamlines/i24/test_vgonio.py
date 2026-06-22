import bluesky.plan_stubs as bps
import pytest
from bluesky import RunEngine
from ophyd_async.core import init_devices

from dodal.devices.beamlines.i24.vgonio import VerticalGoniometer


@pytest.fixture
def vgonio() -> VerticalGoniometer:
    with init_devices(mock=True):
        vgonio = VerticalGoniometer("")
    return vgonio


def test_vertical_gonio_device_can_be_created(vgonio: VerticalGoniometer):
    assert isinstance(vgonio, VerticalGoniometer)


async def test_vgonio_motor_move(vgonio: VerticalGoniometer, run_engine: RunEngine):
    pos = (1.0, 1.5)
    run_engine(bps.mv(vgonio.x, pos[0], vgonio.yh, pos[1]))  # type:ignore

    assert await vgonio.x.user_readback.get_value() == 1.0
    assert await vgonio.yh.user_readback.get_value() == 1.5


def test_device_creation_names(vgonio: VerticalGoniometer):
    assert vgonio._name == "vgonio"
    assert vgonio.omega._name == "vgonio-omega"
