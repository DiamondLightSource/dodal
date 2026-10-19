# How to Write External IO Devices

## Motivation and Overview

At Diamond Dodal devices primarily refer to python classes referencing EPICS channels, with some internal logic.
There are instances when input-output operations are desired that do not work with EPICS.
For example, many GDA-compatible features need disk IO as GDA relies heavily on XML files to define various variables.
One may need a bluesky calibration plan to start with cached values - those could be in the filesystem or a key value store like Redis.

Direct IO inside plans is not allowed when inside the RunEngine context.

As far as is possible, we want our devices to only talk to EPICS PVs. The [config server](https://github.com/DiamondLightSource/daq-config-server) should fulfil the majority of use cases. Where we can't do that, it is possible to make ophyd-async devices, but heavily discouraged and that would be a temporary solution until the config server supports that IO.
It's not recommended to read from the filesystem going forward and instead development effort will be put into the config server.

## Extant examples

- [aperturescatterguard](../../src/dodal/devices/aperturescatterguard.py) - reads a set of valid positions from a file.
- [oav_to_redis_forwarder](../../src/dodal/devices/oav/oav_to_redis_forwarder.py) - pushes data into redis
- [OAV_detector](../../src/dodal/devices/oav/oav_detector.py) - detector configuration is based on a file on disk

## Existing patterns

Those three devices have been mostly at the MX beamlines. To see a more up to date list, narrow down the search to the [beamlines folder](../../src/dodal/beamlines/) and search for a `dls` string. You will see `Path` calls that are about data writing, but also some ALL_CAPS constants such as `DISPLAY_CONFIG`.
There are two cases, either the IO operation we're looking into is just on device start, or it's an ongoing thing. If it's just in the start as a config, the established pattern is to provide a Class for that object, and make a standlone function in the device file to load it from the filesystem, taking path as a parameter.
Then inside the specific file in the beamlines folder, the device takes the product of calling the function with a beamline-specific path. The fact the device just takes an object makes it easier to write mocks for testing.

Conversely if the IO is ongoing throughout the lifetime of the device object, AsyncStatus logic must be implemented, as in the oav_to_redis_forwarder, mentioned earlier.
