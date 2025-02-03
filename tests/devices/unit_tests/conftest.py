import pytest
from bluesky.run_engine import RunEngine

from dodal.beamlines import i03
from dodal.common.beamlines.beamline_utils import clear_devices
from dodal.devices.util.test_utils import patch_motor


@pytest.fixture
def smargon(RE: RunEngine):
    smargon = i03.smargon(connect_immediately=True, mock=True)

    for motor in [smargon.omega, smargon.x, smargon.y, smargon.z]:
        patch_motor(motor)

    yield smargon

    clear_devices()
