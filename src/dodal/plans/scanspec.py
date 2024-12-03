import operator
from functools import reduce
from typing import Annotated, Any

import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
from bluesky.protocols import Movable, Readable
from bluesky.utils import MsgGenerator
from cycler import Cycler, cycler
from ophyd_async.core import (
    StandardDetector,
    StandardFlyer,
)
from ophyd_async.epics.motor import Motor
from ophyd_async.fastcs.panda import (
    HDFPanda,
    StaticSeqTableTriggerLogic,
)
from ophyd_async.plan_stubs import fly_and_collect
from ophyd_async.plan_stubs._fly import (
    prepare_static_seq_table_flyer_and_detectors_with_same_trigger,
)
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


@attach_data_session_metadata_decorator()
def plan(panda: HDFPanda, diff: StandardDetector) -> MsgGenerator:
    trigger_logic = StaticSeqTableTriggerLogic(panda.seq[1])

    flyer = StandardFlyer(
        trigger_logic,
        name="flyer",
    )

    @bpp.stage_decorator(devices=[diff, panda, flyer])
    @bpp.run_decorator()
    def inner():
        yield from prepare_static_seq_table_flyer_and_detectors_with_same_trigger(
            flyer, [diff], number_of_frames=15, exposure=0.1, shutter_time=0.05
        )
        yield from fly_and_collect(
            stream_name="primary",
            flyer=flyer,
            detectors=[diff],
        )

    yield from inner()


@attach_data_session_metadata_decorator()
def plan_step_scan(detectors: set[StandardDetector], motor: Motor) -> MsgGenerator:
    @bpp.stage_decorator(devices=[*detectors, motor])
    @bpp.run_decorator()
    def inner():
        for i in range(10):
            yield from bps.mv(motor, i)
            yield from bps.trigger_and_read((*detectors, motor))

    yield from inner()
