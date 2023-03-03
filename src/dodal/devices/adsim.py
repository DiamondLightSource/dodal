from ophyd import Component, EpicsMotor, MotorBundle


class SimStage(MotorBundle):
    """
    ADSIM EPICS motors
    """

    x: EpicsMotor = Component(EpicsMotor, "M1")
    y: EpicsMotor = Component(EpicsMotor, "M2")
    z: EpicsMotor = Component(EpicsMotor, "M3")
    theta: EpicsMotor = Component(EpicsMotor, "M4")
    load: EpicsMotor = Component(EpicsMotor, "M5")
