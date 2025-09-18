from bluesky.protocols import Readable
from ophyd_async.epics.motor import Motor
from tests.fake_beamline.util import _mock_with_name

from dodal.devices.cryostream import CryoStream


def device_e() -> Readable:
    return _mock_with_name("device_e")


def device_f() -> Motor:
    return _mock_with_name("device_f")


def device_g() -> CryoStream:
    return _mock_with_name("device_g")
