from bluesky.protocols import Readable
from ophyd import EpicsMotor
from ophyd.utils import (
    DestroyedError,
    DisconnectedError,
    UnknownStatusFailure,
)

from dodal.devices.cryostream import Cryo


def device_a() -> Readable:
    raise DestroyedError


def device_b() -> EpicsMotor:
    raise DisconnectedError


def device_c() -> Cryo:
    raise UnknownStatusFailure
