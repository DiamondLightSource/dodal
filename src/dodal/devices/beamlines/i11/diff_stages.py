from typing import Annotated

from ophyd_async.epics.motor import Motor

from dodal.devices.motors import DefaultInfix, Stage


class DiffractometerStage(Stage):
    """This is the diffractometer stage which contains both detectors,
    it allows for rotations and also sample position. Contains:
    theta, delta, two_theta, sample_position.
    """

    theta: Annotated[Motor, DefaultInfix("THETA")]
    delta: Annotated[Motor, DefaultInfix("DELTA")]
    two_theta: Annotated[Motor, DefaultInfix("2THETA")]
    sample_position: Annotated[Motor, DefaultInfix("SPOS")]


class DiffractometerBase(Stage):
    """This is the diffractometer stage which contains both detectors,
    it allows for translation about x and y and also sample position. Contains:
    x1, x2, y1, y2, y3. Used for aligning the detector to the beam/sample.
    """

    x1: Annotated[Motor, DefaultInfix("X1")]
    x2: Annotated[Motor, DefaultInfix("X2")]
    y1: Annotated[Motor, DefaultInfix("Y1")]
    y2: Annotated[Motor, DefaultInfix("Y2")]
    y3: Annotated[Motor, DefaultInfix("Y3")]
