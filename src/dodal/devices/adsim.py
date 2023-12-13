from ophyd import Component, EpicsMotor, MotorBundle


class SimStage(MotorBundle):
    """
    ADSIM EPICS motors
    """

    x = Component(EpicsMotor, "M1")
    y = Component(EpicsMotor, "M2")
    z = Component(EpicsMotor, "M3")
    theta = Component(EpicsMotor, "M4")
    load = Component(EpicsMotor, "M5")
