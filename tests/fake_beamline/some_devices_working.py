from bluesky.protocols import Readable
from ophyd_async.epics.motor import Motor
from tests.fake_beamline.util import _mock_with_name

from dodal.devices.undulator import Undulator


def device_a() -> Readable:
    return _mock_with_name("readable")


def device_b() -> Motor:
    raise TimeoutError


def device_c() -> Undulator:
    return _mock_with_name("undulator")
