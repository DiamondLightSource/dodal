from enum import IntEnum

from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor, EpicsSignal, EpicsSignalRO


class ShutterState(IntEnum):
    CLOSED = 0
    OPEN = 1


class DetectorMotion(Device):
    """Physical motion and interlocks for detector travel"""

    upstream_x = Cpt(EpicsMotor, "-MO-DET-01:UPSTREAMX")
    downstream_x = Cpt(EpicsMotor, "-MO-DET-01:DOWNSTREAMX")
    x = Cpt(EpicsMotor, "-MO-DET-01:X")
    y = Cpt(EpicsMotor, "-MO-DET-01:Y")
    z = Cpt(EpicsMotor, "-MO-DET-01:Z")
    yaw = Cpt(EpicsMotor, "-MO-DET-01:YAW")
    shutter = Cpt(EpicsSignal, "-MO-DET-01:SET_SHUTTER_STATE")  # 0=closed, 1=open
    #   monitors
    shutter_closed_lim = Cpt(
        EpicsSignalRO, "-MO-DET-01:CLOSE_LIMIT"
    )  # on limit = 1, off = 0
    shutter_open_lim = Cpt(
        EpicsSignalRO, "-MO-DET-01:OPEN_LIMIT"
    )  # on limit = 1, off = 0
    z_disabled = Cpt(
        EpicsSignalRO, "-MO-DET-01:Z:DISABLED"
    )  # robot interlock, 0=ok to move, 1=blocked
    crate_power = Cpt(
        EpicsSignalRO, "-MO-PMAC-02:CRATE2_HEALTHY"
    )  # returns 0 if no power
    in_robot_load_safe_position = Cpt(
        EpicsSignalRO, "-MO-PMAC-02:GPIO_INP_BITS.B2"
    )  # returns 1 if safe
