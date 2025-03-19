from pathlib import Path

from ophyd_async.epics.adsimdetector import SimDetector

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import DET_SUFFIX, HDF5_SUFFIX
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.adsim import SimStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

BL = "adsim"
PREFIX = BeamlinePrefix("t01")
set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/tmp"),
        client=LocalDirectoryServiceClient(),
    )
)

"""
Beamline module for use with the simulated AreaDetector and motors.
These devices are simulated at the EPICS level, enabling testing of
dodal and ophyd-async against what appear to be "real" signals.

Usage Example
-------------

Start the simulated beamline by following the epics-containers tutorial at
https://epics-containers.github.io/main/tutorials/launch_example.html
And ensure that the signals are visible:

```sh
export EPICS_CA_ADDR_LIST=127.0.0.1:5094
```

How to use the devices in a plan:
In an ipython terminal run:

```python
from bluesky.run_engine import RunEngine

from dodal.beamlines.adsim import det, stage
from dodal.plans import count

RE = RunEngine()
d = det(connect_immediately=True)
s = stage(connect_immediately=True)
RE(count([d], num=10))
```

"""


@device_factory()
def stage() -> SimStage:
    return SimStage(f"{PREFIX.beamline_prefix}-MO-SIMC-01:")


@device_factory()
def det() -> SimDetector:
    return SimDetector(
        f"{PREFIX.beamline_prefix}-DI-CAM-01:",
        path_provider=get_path_provider(),
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )
