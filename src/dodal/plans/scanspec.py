import operator
from functools import reduce
from typing import Annotated, Any

import bluesky.plans as bp
from bluesky.protocols import Movable, Readable
from cycler import Cycler, cycler
from pydantic import Field, validate_call
from scanspec.specs import Spec

from dodal.common import MsgGenerator
from dodal.plan_stubs.data_session import attach_data_session_metadata_decorator


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def spec_scan(
    detectors: Annotated[
        set[Readable],
        Field(
            description="Set of readable devices, will take a reading at each point, \
            in addition to any Movables in the Spec",
        ),
    ],
    spec: Annotated[
        Spec[Movable],
        Field(description="ScanSpec modelling the path of the scan"),
    ],
    metadata: dict[str, Any] | None = None,
) -> MsgGenerator:
    """Generic plan for reading `detectors` at every point of a ScanSpec `Spec`.
    A `Spec` is an N-dimensional path.
    """
    # TODO: https://github.com/bluesky/scanspec/issues/154
    # support Static.duration: Spec[Literal["DURATION"]]

    _md = {
        "plan_args": {
            "detectors": {det.name for det in detectors},
            "spec": repr(spec),
        },
        "plan_name": "spec_scan",
        "shape": spec.shape(),
        **(metadata or {}),
    }

    yield from bp.scan_nd(tuple(detectors), _as_cycler(spec), md=_md)


def _as_cycler(spec: Spec[Movable]) -> Cycler:
    """
    Convert a scanspec to a cycler for compatibility with legacy Bluesky plans such as
    `bp.scan_nd`. Use the midpoints of the scanspec since cyclers are normally used
    for software triggered scans.

    Args:
        spec: A scanspec

    Returns:
        Cycler: A new cycler
    """

    midpoints = spec.frames().midpoints
    # Need to "add" the cyclers for all the axes together. The code below is
    # effectively: cycler(motor1, [...]) + cycler(motor2, [...]) + ...
    return reduce(operator.add, (cycler(*args) for args in midpoints.items()))
