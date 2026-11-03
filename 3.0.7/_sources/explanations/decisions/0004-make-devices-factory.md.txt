# 4. Add device factory decorator with lazy connect support

Date: 2024-04-26

## Status

Accepted

## Context

Device instances should be capable of being created without necessarily connecting, so long as they are connected prior to being utilised to collect data. The current method puts requirements on the init method of device classes, and does not expose all options for connecting to ophyd-async devices.

## Decision

DAQ members led us to this proposal:

- ophyd-async: make Device.connect(mock, timeout, force=False) idempotent
- ophyd-async: make ensure_connected(\*devices) plan stub
- dodal: make device_factory() decorator that may construct, name, cache and connect a device
- dodal: collect_factories() returns all device factories
- blueapi: call collect_factories(), instantiate and connect Devices appropriately, log those that fail
- blueapi: when plan is called, run ensure_connected on all plan args and defaults that are Devices

We can then iterate on this if the parallel connect causes a broadcast storm. We could also in future add a monitor to a heartbeat PV per device in Device.connect so that it would reconnect next time it was called.

## Consequences

Beamlines will be converted to use the decorator, and default arguments to plans should be replaced with a non-eagerly connecting call to the initializer controlling device.
