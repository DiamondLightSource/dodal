from ophyd import Component as Cpt
from ophyd import EpicsMotor
from ophyd.epics_motor import MotorBundle


class VmxmSampleMotors(MotorBundle):
    omega: EpicsMotor = Cpt(EpicsMotor, "OMEGA")
