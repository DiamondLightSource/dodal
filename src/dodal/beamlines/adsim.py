from ophyd_async.epics.adsimdetector import SimDetector

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import DET_SUFFIX, HDF5_SUFFIX
from dodal.device_manager import DeviceManager
from dodal.devices.motors import XThetaStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

BL = "adsim"
PREFIX = BeamlinePrefix("t01")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


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
export EPICS_CA_ADDR_LIST=127.0.0.1:9064
export EPICS_CA_NAME_SERVERS=127.0.0.1:9064
export EPICS_PVA_NAME_SERVERS=127.0.0.1:9075
```

How to use the devices in a plan:
In an ipython terminal run:

```python
from bluesky.run_engine import RunEngine

from dodal.beamlines.adsim import devices
from dodal.plans import count


run_engine = RunEngine()

built = devices.build_and_connect().or_raise()
d = built["det"]
s = built["stage"]

run_engine(count([d], num=10))
```
"""


@devices.fixture
def path_provider():
    # This fixture is only used if a path_provider is not passed to the device
    # manager when the devices are built.
    #
    # When used via blueAPI with numtracker enabled, it will take priority and
    # the path provider here will not be created.
    from pathlib import Path

    from ophyd_async.core import StaticPathProvider, UUIDFilenameProvider

    return StaticPathProvider(
        UUIDFilenameProvider(),
        Path("/tmp"),  # The directory for `det` to write to- may be mounted as a volume
    )


@devices.factory()
def stage() -> XThetaStage:
    return XThetaStage(
        f"{PREFIX.beamline_prefix}-MO-SIMC-01:", x_infix="M1", theta_infix="M2"
    )


@devices.factory()
def det(path_provider) -> SimDetector:
    return SimDetector(
        f"{PREFIX.beamline_prefix}-DI-CAM-01:",
        path_provider=path_provider,
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )
