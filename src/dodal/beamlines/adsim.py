from pathlib import Path

from ophyd_async.epics.adsimdetector import SimDetector

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.adsim.simstage import SimStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("bl01t")
set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/dev/null"),
        client=LocalDirectoryServiceClient(),
    )
)

"""
Usage Example
-------------

Start the simulated beamline by following the epics-containers tutorial at
https://epics-containers.github.io/main/tutorials/launch_example.html

```bash
    git clone https://github.com/epics-containers/example-services
    cd example-services
    # setup some environment variables
    source ./environment.sh
    docker compose up -d
```


How to use the devices in a plan:
In an ipython terminal run:

```python
    from bluesky.plans import count, grid_scan
    from bluesky.run_engine import RunEngine

    from dodal.beamlines.adsim import adsim, sim_motors
    from dodal.common.beamlines.beamline_utils import get_path_provider

    RE = RunEngine()
    det = adsim(connect_immediately=True)
    motors = sim_motors(connect_immediately=True)
    pp = get_path_provider()
    await pp.update()
    RE(count([det], num=10))
    RE(grid_scan([det], motors.x, 0, 10, 11, motors.y, 0, 10, 11))


```

"""


@device_factory()
def sim_motors() -> SimStage:
    return SimStage(BL + "-MO-SIM-01:")


@device_factory()
def adsim() -> SimDetector:
    return SimDetector(
        BL + "-DI-CAM-01:",
        hdf_suffix="HDF:",
        drv_suffix="DET:",
        path_provider=get_path_provider(),
    )
