# Plan Standards

> [!NOTE]
> These are some notes on how to write plans . Plans should not be implemented in dodal (unless very general).

## Use a list of standard baseline devices


Bluesky has a standard preprocesser/plan decorator baseline_decorator that reads from a collection of Readable devices at the start and end of every plan.

These devices are usually not included in the scan logic (e.g. upstream optical components). They are likely to be consistent across multiple plans, although they may be overridden by explicitly passed arguments.


### Example: besaline devices implementation and use for I22

```python
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
