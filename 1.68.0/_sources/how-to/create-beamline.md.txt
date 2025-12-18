# Creating a new beamline

A beamline is a collection of devices that can be used together to run experiments, they may be read-only or capable of being set.
They include motors in the experiment hutch, optical components in the optics hutch, the synchrotron "machine" and more.

## Beamline Modules

Each beamline should have its own file in the ``dodal.beamlines`` folder, in which the particular devices for the
beamline are instantiated. The file should be named after the colloquial name for the beamline. For example:

* ``i03.py``
* ``i20_1.py``
* ``vmxi.py``

Beamline modules (in ``dodal.beamlines``) are code-as-configuration. They define the set of devices and common device
settings needed for a particular beamline or group of similar beamlines (e.g. a beamline and its digital twin). Some
of our tooling depends on the convention of *only* beamline modules going in this package. Common utilities should
go somewhere else e.g. ``dodal.utils`` or ``dodal.beamlines.common``.

The following example creates a fictitious beamline ``w41``, with a simulated twin ``s41``.
``w41`` needs to monitor the status of the Synchrotron and has an AdAravisDetector.
``s41`` has a simulated clone of the AdAravisDetector, but not of the Synchrotron machine.

```python

    from functools import cache
    from pathlib import Path
    from ophyd_async.core import PathProvider
    from ophyd_async.epics.adaravis import AravisDetector

    from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
    from dodal.common.beamlines.device_helpers import CAM_SUFFIX, HDF5_SUFFIX
    from dodal.common.visit import RemoteDirectoryServiceClient, StaticVisitPathProvider
    from dodal.device_manager import DeviceManager
    from dodal.devices.synchrotron import Synchrotron
    from dodal.log import set_beamline as set_log_beamline
    from dodal.utils import BeamlinePrefix, get_beamline_name

    BL = get_beamline_name("s41")  # Default used when not on a live beamline
    PREFIX = BeamlinePrefix(BL)
    set_log_beamline(BL)  # Configure logging and util functions
    set_utils_beamline(BL)

    devices = DeviceManager()
    
    @devices.fixture
    @cache
    def path_provider() -> PathProvider:
        # Currently we must hard-code the visit, determining the visit is WIP.
        return StaticVisitPathProvider(
            BL,
            # Root directory for all detectors
            Path("/dls/w41/data/YYYY/cm12345-1"),
            # Uses an existing GDA server to ensure filename uniqueness
            client=RemoteDirectoryServiceClient("http://s41-control:8088/api"),
            # Else if no GDA server use a LocalDirectoryServiceClient(),
        )


    """
    Define device factory functions below this point.
    A device factory function is any function that has a return type which conforms
    to one or more Bluesky Protocols.
    """

    """
    This decorator gives extra desirable behaviour to this factory function:
    - it may be instantiated automatically, selectively on live beamline
    - it automatically names the device if no name is explicitly set
    - it may be skipped when make_all_devices is called on this module
    - it must be explicitly connected (which may be automated by tools)
        - when connected it may connect to a simulated backend
        - it may be connected concurrently (when automated by tools)
    """
    @devices.factory(skip = BL == "s41")
    def synchrotron() -> Synchrotron:
        return Synchrotron()


    @devices.factory()
    def d11(path_provider: PathProvider) -> AravisDetector:
        return AravisDetector(
            f"{PREFIX.beamline_prefix}-DI-DCAM-01:",
            path_provider=path_provider,
            drv_suffix=CAM_SUFFIX,
            fileio_suffix=HDF5_SUFFIX,
        )
```
