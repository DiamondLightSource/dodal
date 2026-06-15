import pytest
from ophyd_async.core import init_devices

from dodal.devices.beamlines.i15_1.puck_detector import PuckDetect


@pytest.mark.requires(instrument="i15-1")  # connects to the real beamline
async def test_puck_detect_can_connect_to_real_detection_webpage():
    async with init_devices(mock=True):
        puck_detect = PuckDetect("https://i15-1-cam3-processing.diamond.ac.uk/result")

    await puck_detect.trigger()
