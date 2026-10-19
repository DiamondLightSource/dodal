# Converting an existing beamline to use a DeviceManager

This guide assumes you have a beamline module file (eg `dodal/beamlines/ixx.py`)
with a number of functions defined and decorated with `@device_factory`
(`dodal.common.beamlines.beamline_utils`).

## Create a DeviceManager

By convention this should be named `devices` but can be custom if there is good
reason.

```python
from dodal.device_manager import DeviceManager

devices = DeviceManager()
```

This device manager keeps track of all device factories for a beamline making it
easier to determine which are present and the order in which to build them to
ensure dependencies are available before their dependents.

## Replace the `@device_factory` decorators

Each factory function should be decorated with `@devices.factory` (where
`devices` is the name of the `DeviceManager` created above) instead of
`@device_factory`. If no arguments are required, the parentheses can be omitted,
eg

```python
@devices.factory()
def device() -> Device:
    ...
```

is equivalent to

```python
@devices.factory
def device() -> Device:
    ...
```

If arguments (eg `skip` or `mock`) were passed to `device_factory`, these can
continue to be passed to `devices.factory` in the same way.

## Replace `get_path_provider` with fixture

Previously, the path_provider used by detectors was set and accessed as a global.

Where device factory functions used this global (via `get_path_provider`) they
should be updated to accept `path_provider` as a parameter. This can then be
passed in when creating the devices.

```python
# Previous approach using `get_path_provider`...
@device_factory()
def panda() -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=get_path_provider(),
    )

# ... should be replaced with
@devices.factory()
def panda(path_provider: PathProvider) -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=path_provider,
    )
```

Where a beamline was setting the path provider via `set_path_provider`, a
fixture should be created which will provide a fallback instance to be used if
one is not passed in.


```python
# The previous approach...
set_path_provider(PathProviderImplementation(...))

# ...should be removed and replaced with
@devices.fixture
def path_provider() -> PathProvider:
    return PathProviderImplementation(...)
```

## Replace factory calls with parameters

Where one function previously called another to access another device, this should
be replaced with a parameter of the same name. This is to prevent multiple
instances of devices being created as functions no longer cache the devices they
create.

```python
# Previous example using a device factory function
@device_factory()
def beamsize() -> Beamsize:
    return Beamsize(aperture_scatterguard())

# New version with `aperture_scatterguard` passed as a parameter
@devices.factory
def beamsize(aperture_scatterguard: ApertureScatterguard) -> Beamsize:
    return Beamsize(aperture_scatterguard)
```

## Merge multiple device managers

If devices need to be shared between multiple beamlines, eg branch beamlines
sharing optics components, an external device manager can be imported and
merged into another.

```python
# in ixx_shared.py
devices = DeviceManager()

@devices.factory
def common_device() -> CommonDevice:
   ...

# in ixx.py
from ixx_shared import devices as shared_devices

devices = DeviceManager()
devices.include(shared_devices)

# devices defined in the common beamline module can then be used as dependencies
# in the beamline module
@devices.factory
def beamline_device(common_device: CommonDevice) -> BeamlineDevice:
    ...
```
