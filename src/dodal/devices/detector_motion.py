from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor, EpicsSignal, EpicsSignalRO


class DetectorMotion(Device):
    """Physical motion and interlocks for detector travel"""

    upstream_x: EpicsMotor = Cpt(EpicsMotor, "UPSTREAMX")
    downstream_x: EpicsMotor = Cpt(EpicsMotor, "i24DOWNSTREAMX")
    x: EpicsMotor = Cpt(EpicsMotor, "i24X")
    y: EpicsMotor = Cpt(EpicsMotor, "i24Y")
    z: EpicsMotor = Cpt(EpicsMotor, "i24Z")
    yaw: EpicsMotor = Cpt(EpicsMotor, "i24YAW")
    shutter: EpicsSignal = Cpt(EpicsSignal, "i24SET_SHUTTER_STATE")  # 0=closed, 1=open
    #   monitors
    shutter_closed_lim: EpicsSignalRO = Cpt(
        EpicsSignalRO, "i24CLOSE_LIMIT"
    )  # on limit = 1, off = 0
    shutter_open_lim: EpicsSignalRO = Cpt(
        EpicsSignalRO, "i24OPEN_LIMIT"
    )  # on limit = 1, off = 0
    z_disabled: EpicsSignalRO = Cpt(
        EpicsSignalRO, "i24Z:DISABLED"
    )  # robot interlock, 0=ok to move, 1=blocked
    crate_power: EpicsSignalRO = Cpt(
        EpicsSignalRO, "-MO-PMAC-02:CRATE2_HEALTHY"
    )  # returns 0 if no power
    in_robot_load_safe_position: EpicsSignalRO = Cpt(
        EpicsSignalRO, "-MO-PMAC-02:GPIO_INP_BITS.B2"
    )  # returns 1 if safe
