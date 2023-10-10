import asyncio
from unittest.mock import patch

import pytest
from bluesky.run_engine import RunEngine, TransitionError

EXPECTED_DEVICES = ["PANDA", "D12", "D11"]

with patch.dict("os.environ", {"BEAMLINE": "p38"}, clear=True):
    from dodal.beamlines import p38
    from dodal.utils import make_all_devices


@pytest.fixture(scope="function")
def RE(request):
    loop = asyncio.new_event_loop()
    loop.set_debug(True)
    RE = RunEngine({}, call_returns_result=True, loop=loop)

    def clean_event_loop():
        if RE.state not in ("idle", "panicked"):
            try:
                RE.halt()
            except TransitionError:
                pass
        loop.call_soon_threadsafe(loop.stop)
        RE._th.join()
        loop.close()

    request.addfinalizer(clean_event_loop)
    return RE


def test_device_creation(RE):
    devices = make_all_devices(p38, sim=True)
    assert len(devices) > 0
    for device_name in devices.keys():
        assert device_name in EXPECTED_DEVICES
    assert len(EXPECTED_DEVICES) == len(devices)
