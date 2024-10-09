from pathlib import Path

from ophyd_async.epics.adsimdetector import SimDetector

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.adsim import SimStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_hostname

BL = get_hostname()
set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/scratch/adsim/bluesky"),
        client=LocalDirectoryServiceClient(),
    )
)

"""
Usage Example
-------------

Before running the code, make sure to perform the following steps:

1. Run AdSimulator on the workstation using DLS Launcher.
2. Export the following environment variables:
    - EPICS_CA_SERVER_PORT=6064
    - EPICS_CA_REPEATER_PORT=6065

The code below demonstrates how to use the `adsim` and `sim_motors` functions from the `dodal.beamlines.adsim` module:

```
import asyncio

from bluesky.plans import count
from bluesky.run_engine import RunEngine

from dodal.beamlines.adsim import adsim, sim_motors
from dodal.common.beamlines.beamline_utils import get_path_provider


async def run_experiment():
    RE = RunEngine()
    det = adsim()
    sim_motors()
    pp = get_path_provider()
    await pp.update()
    RE(count([det], num=10))


if __name__ == "__main__":
    asyncio.run(run_experiment())
```

"""


def sim_motors(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> SimStage:
    return device_instantiation(
        SimStage,
        "sim_motors",
        BL + "-MO-SIM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
    )


def adsim(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> SimDetector:
    return device_instantiation(
        SimDetector,
        "adsim",
        BL + "-AD-SIM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix="CAM:",
        hdf_suffix="HDF5:",
        path_provider=get_path_provider(),
        bl_prefix=False,
    )
