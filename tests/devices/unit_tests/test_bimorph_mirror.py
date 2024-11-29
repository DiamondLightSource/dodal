import asyncio

from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector

from dodal.devices.bimorph_mirror import BimorphMirror

RE = RunEngine()


async def async_main():
    with DeviceCollector(mock=True):
        bm = BimorphMirror(prefix="BL02J-EA-IOC-97:G0:", number_of_channels=8)
    out = await bm.read()
    print(out)

    await bm.set({1: 10.0})
    print("\n")

    out = await bm.read()
    print(out)


asyncio.run(async_main())
