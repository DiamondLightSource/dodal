from pathlib import PurePath
from ophyd.epics_motor import EpicsMotor
from ophyd_async.core import PathProvider, StaticPathProvider, UUIDFilenameProvider
from ophyd_async.epics.adsimdetector import SimDetector

from dodal.device_manager import DeviceManager
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import DET_SUFFIX, HDF5_SUFFIX
from dodal.devices.motors import XThetaStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

BL = "adsim"
PREFIX = BeamlinePrefix("t01")
set_log_beamline(BL)
set_utils_beamline(BL)


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
from pathlib import Path

from bluesky.run_engine import RunEngine
from ophyd_async.core import StaticPathProvider, UUIDFilenameProvider

from dodal.beamlines.adsim import det, stage
from dodal.common.beamlines.beamline_utils import set_path_provider
from dodal.plans import count


set_path_provider(
    StaticPathProvider(
        UUIDFilenameProvider(),
        "/tmp", # The directory for `det` to write to- may be mounted as a volume
    )
)

run_engine = RunEngine()
d = det(connect_immediately=True)
s = stage(connect_immediately=True)
run_engine(count([d], num=10))
```

"""

devices = DeviceManager()


@devices.fixture
def path_provider() -> PathProvider:
    return StaticPathProvider(UUIDFilenameProvider(), PurePath("/"))


@devices.factory(timeout=2, mock=False)
def stage() -> XThetaStage:
    return XThetaStage(
        f"{PREFIX.beamline_prefix}-MO-SIMC-01:", x_infix="M1", theta_infix="M2"
    )


@devices.factory(timeout=2)
def det(path_provider: PathProvider) -> SimDetector:
    return SimDetector(
        f"{PREFIX.beamline_prefix}-DI-CAM-01:",
        path_provider=path_provider,
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )


@devices.v1_init(factory=EpicsMotor, prefix=f"{PREFIX.beamline_prefix}-MO-SIMC-01:M1")
def old_motor(motor: EpicsMotor):
    # arbitrary post-init configuration
    motor.settle_time = 12
