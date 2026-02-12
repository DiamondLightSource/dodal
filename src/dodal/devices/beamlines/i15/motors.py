from typing import Annotated

from ophyd_async.epics.motor import Motor

from dodal.devices.motors import Infix, Stage


class UpstreamDownstreamPair(Stage):
    upstream: Annotated[Motor, Infix("US")]
    downstream: Annotated[Motor, Infix("DS")]


class NumberedTripleAxisStage(Stage):
    axis1: Annotated[Motor, Infix("AXIS1")]
    axis2: Annotated[Motor, Infix("AXIS2")]
    axis3: Annotated[Motor, Infix("AXIS3")]
