import pytest
from ophyd.sim import make_fake_device

from dodal.devices.focusing_mirror import FocusingMirror


@pytest.fixture
def vfm() -> FocusingMirror:
    mirror: FocusingMirror = make_fake_device(FocusingMirror)
    return mirror


def test_mirror_set_voltage_sets_and_waits(vfm: FocusingMirror):
    pass
