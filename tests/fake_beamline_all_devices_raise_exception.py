import asyncio

from bluesky.protocols import Readable
from ophyd_async.epics.motor import Motor

from dodal.devices.cryostream import CryoStream


def device_a() -> Readable:
    raise TimeoutError


def device_b() -> Motor:
    raise asyncio.TimeoutError


def device_c() -> CryoStream:
    raise ValueError
