from ophyd import Component as Cpt
from ophyd import EpicsMotor
from ophyd.epics_motor import MotorBundle


class VGonio(MotorBundle):
    x: EpicsMotor = Cpt(EpicsMotor, "PINX")
    z: EpicsMotor = Cpt(EpicsMotor, "PINZ")
    yh: EpicsMotor = Cpt(EpicsMotor, "PINYH")
    omega: EpicsMotor = Cpt(EpicsMotor, "OMEGA")
    kappa: EpicsMotor = Cpt(EpicsMotor, "KAPPA")
    phi: EpicsMotor = Cpt(EpicsMotor, "PHI")

    # Real motors
    xs: EpicsMotor = Cpt(EpicsMotor, "PINXS")
    ys: EpicsMotor = Cpt(EpicsMotor, "PINXS")
    zs: EpicsMotor = Cpt(EpicsMotor, "PINZS")
