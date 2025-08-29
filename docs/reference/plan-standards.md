# Plan Standards

> [!NOTE]
> This is meant as a collection of guidelines on plan standards using dodal devices.
> As a general rule, beamline/technique specific plans should not be in dodal.


## Use a list of standard baseline devices


Bluesky has a standard preprocessor/plan decorator [baseline_decorator](https://blueskyproject.io/bluesky/main/generated/bluesky.preprocessors.baseline_decorator.html#bluesky.preprocessors.baseline_decorator) that reads from a collection of Readable devices which are not usually included in the plan logic at the start and end of every plan.



### Example: besaline devices implementation and use for I22

In this example, a set of Readable devices from the optics hutch is defined by injecting all the devices that we want to read at the start and end of the plan, while not being used directly in the plan logic.

```python
# In sas_bluesky/baseline.py
from bluesky.protocols import Readable
from dodal.common import inject

DEFAULT_BASELINE_MEASUREMENTS: set[Readable] = {
    inject("fswitch"),
    inject("slits_1"),
    inject("slits_2"),
    inject("slits_3"),
    inject("slits_4"),
    inject("slits_5"),
    inject("slits_6"),
    inject("hfm"),
    inject("vfm"),
    inject("undulator"),
    inject("dcm"),
    inject("synchrotron"),
}
```

This set of devices is passed to the `baseline_decorator` which decorates the `inner_plan`. This decorator will record a reading from all devices after `open_run` and emit an event document with metadata from all those devices.

```python
from typing import Any

import bluesky.preprocessors as bpp
import bluesky.plans as bp
from bluesky.protocols import Readable
from bluesky.utils import MsgGenerator

from sas_bluesky.baseline import (
    DEFAULT_BASELINE_MEASUREMENTS,
)

_PLAN_NAME = "stopflow"

def experiment(
    experiment_detector: Readable,
    experiment_param: int,
    baseline: set[Readable] = DEFAULT_BASELINE_MEASUREMENTS,
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:

    # Collect metadata
    plan_args = {
        "experiment_device": experiment_detector.name,
        "experiment_param": experiment_param,
        "baseline": {device.name + ":" + repr(device) for device in baseline},
    }

    _md = {
        "detectors": {experiment_detector.name},
        "plan_args": plan_args,
        "hints": {},
    }
    _md.update(metadata or {})

    @bpp.baseline_decorator(baseline)
    @bpp.stage_decorator([experiment_detector])
    @bpp.run_decorator(md=_md)
    def inner_plan():
        yield from bp.count([experiment_detector], experiment_param)

    yield from inner_plan()
```
