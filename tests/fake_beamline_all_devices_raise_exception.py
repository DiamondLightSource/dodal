import asyncio

from bluesky.protocols import Readable
from ophyd_async.epics.motion import Motor

from dodal.devices.undulator import Undulator


def device_a() -> Readable:
    raise TimeoutError


def device_b() -> Motor:
    raise asyncio.TimeoutError


def device_c() -> Undulator:
    raise ValueError
