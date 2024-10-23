# Include Devices in Plans

There are two main ways to include dodal devices in plans

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

def my_plan(detector: Readable = i22.saxs()) -> MsgGenerator:
    yield from bp.count([detector])

RE(my_plan()))
```

This is useful for plans that will usually, but not exclusively, use the same device or that are designed to only ever work with a specific device.
