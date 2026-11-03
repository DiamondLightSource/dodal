import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.b01_1.flip_mirror import FlipMirror


@pytest.fixture
def flip_mirror() -> FlipMirror:
    with init_devices(mock=True):
        flip_mirror = FlipMirror("BLXX-EA-FLIP-01:")
    return flip_mirror


def test_flip_mirror_uses_fastcs_pvs(flip_mirror: FlipMirror):
    assert flip_mirror.position.source == "mock+ca://BLXX-EA-FLIP-01:Position_RBV"


async def test_flip_mirror_reads_position(flip_mirror: FlipMirror):
    set_mock_value(flip_mirror.position, True)
    await assert_reading(flip_mirror, {"flip_mirror-position": partial_reading(True)})


@pytest.mark.parametrize("value", [True, False])
async def test_flip_mirror_can_be_moved(
    flip_mirror: FlipMirror, run_engine: RunEngine, value: bool
):
    set_mock_value(flip_mirror.position, not value)
    run_engine(bps.mv(flip_mirror, value))
    assert await flip_mirror.position.get_value() is value
