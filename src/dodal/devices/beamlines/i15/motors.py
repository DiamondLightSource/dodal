from typing import Annotated

from ophyd_async.epics.motor import Motor

from dodal.devices.motors import DefaultInfix, Stage


class UpstreamDownstreamPair(Stage):
    upstream: Annotated[Motor, DefaultInfix("US")]
    downstream: Annotated[Motor, DefaultInfix("DS")]


class NumberedTripleAxisStage(Stage):
    axis1: Annotated[Motor, DefaultInfix("AXIS1")]
    axis2: Annotated[Motor, DefaultInfix("AXIS2")]
    axis3: Annotated[Motor, DefaultInfix("AXIS3")]
