from dataclasses import dataclass
import os
from pathlib import Path

from dodal.devices.areadetector import AdSimDetector

from .utils import get_hostname


from ophyd_async.core import DeviceCollector, StaticDirectoryProvider
from ophyd_async.epics.motion import Motor

# Default prefix to hostname unless overriden with export PREFIX=<prefix>
PREFIX: str = os.environ.get("PREFIX", get_hostname())


@dataclass
class SimStage:
    x: Motor
    y: Motor
    z: Motor
    theta: Motor
    load: Motor


async def stage(
    name: str = "sim_motors",
    sim: bool = False,
) -> SimStage:
    async with DeviceCollector(sim=sim):
        x = Motor(name=name, prefix=f"{PREFIX}-MO-SIM-01:M1")
        y = Motor(name=name, prefix=f"{PREFIX}-MO-SIM-01:M2")
        z = Motor(name=name, prefix=f"{PREFIX}-MO-SIM-01:M3")
        theta = Motor(name=name, prefix=f"{PREFIX}-MO-SIM-01:M4")
        load = Motor(name=name, prefix=f"{PREFIX}-MO-SIM-01:M5")
    return SimStage(x, y, z, theta, load)


def det(
    name: str = "adsim",
    sim: bool = False,
) -> AdSimDetector:
    with DeviceCollector(sim=sim):
        adsim = AdSimDetector(
            name,
            f"{PREFIX}-AD-SIM-01:",
            StaticDirectoryProvider("/tmp", "adsim"),
        )
    return adsim


if __name__ == "__main__":
    import bluesky.plans as bp
    from bluesky import RunEngine

    RE = RunEngine()
    d = det()
    docs = []
    RE(bp.count([d]), lambda name, doc: docs.append({"name": name, "doc": doc}))

    import json

    print(json.dumps(docs))
