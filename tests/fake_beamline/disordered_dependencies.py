from bluesky.protocols import Readable
from ophyd_async.epics.motor import Motor
from tests.fake_beamline.util import _mock_with_name

from dodal.devices.cryostream import CryoStream


def device_z(device_x: Readable, device_y: Motor) -> CryoStream:
    return _mock_with_name("cryo")


def device_x() -> Readable:
    return _mock_with_name("readable")


def device_y() -> Motor:
    return _mock_with_name("motor")
