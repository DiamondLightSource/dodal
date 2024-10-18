# Include Devices in Plans

There are three main ways to include dodal devices in plans

## 1. Pass as Argument

```python
import bluesky.plans as bp

from bluesky.protocols import Readable
from bluesky.utils import MsgGenerator
from dodal.beamlines import i22

def my_plan(detector: Readable) -> MsgGenerator:
    yield from bp.count([detector])

RE(my_plan(i22.saxs()))
```

This is useful for generic plans that can run on a variety of devices and are not designed with any specific device in mind.

## 2. Pass as Default Argument

```python
import bluesky.plans as bp

from bluesky.protocols import Readable
from bluesky.utils import MsgGenerator
from dodal.beamlines import i22

def my_plan(detector: Readable = i22.saxs(connect_immediately=False)) -> MsgGenerator:
    yield from bp.count([detector])

RE(my_plan()))
```

This is useful for plans that will usually, but not exclusively, use the same device.

## 3. Instantiate Within the Plan

```python
import bluesky.plans as bp
import ophyd_async.plan_stubs as ops

from bluesky.protocols import Readable
from bluesky.utils import MsgGenerator
from dodal.beamlines import i22

def my_plan() -> MsgGenerator:
    detector = i22.saxs(connect_immediately=False)
    # We need to connect via the stub instead of directly 
    # so that the RunEngine performs the connection in the
    # correct event loop
    yield from ops.ensure_connected(detector)
    yield from bp.count([detector])

RE(my_plan()))
```

This is useful for plans that are designed to only ever work with a specific device.
