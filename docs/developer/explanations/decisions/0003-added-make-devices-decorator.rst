3. Add device factory decorator with lazy connect support
=========================================================

Date: 2024-04-26

Status
------

Accepted

Context
-------

We should add a decorator to support verfied device connection.

Decision
--------

DAQ members led us to this proposal:

- ophyd-async: make Device.connect(mock, timeout, force=False) be idempotent
- ophyd-async: make ensure_connected(\*devices) plan stub
- dodal: make device_factory(startup_connect=False) decorator that makes, names, caches and optionally connects a device
- dodal: make get_device_factories() that returns all device factories and whether they should be connected at startup
- blueapi: call get_device_factories(), make all the Devices, connect the ones that should be connected at startup in parallel and log those that fail
- blueapi: when plan is called, run ensure_connected on all plan args and defaults that are Devices

We can then iterate on this if the parallel connect causes a broadcast storm. We could also in future add a monitor to a heartbeat PV per device in Device.connect so that it would reconnect next time it was called.

Consequences
------------

The changes above.
