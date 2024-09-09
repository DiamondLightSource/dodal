import pytest
from bluesky.run_engine import RunEngine

from dodal.beamlines import i03
from dodal.common.beamlines.beamline_utils import clear_devices
from dodal.devices.util.test_utils import patch_motor


@pytest.fixture
def smargon(RE: RunEngine):
    smargon = i03.smargon(fake_with_ophyd_sim=True)

    for motor in [smargon.omega, smargon.x, smargon.y, smargon.z]:
        patch_motor(motor)

    yield smargon

    clear_devices()
