from ophyd import Component as Cpt
from ophyd import EpicsMotor
from ophyd.epics_motor import MotorBundle


class VGonio(MotorBundle):
    x = Cpt(EpicsMotor, "PINX")
    z = Cpt(EpicsMotor, "PINZ")
    yh = Cpt(EpicsMotor, "PINYH")
    omega = Cpt(EpicsMotor, "OMEGA")
    kappa = Cpt(EpicsMotor, "KAPPA")
    phi = Cpt(EpicsMotor, "PHI")

    # Real motors
    xs = Cpt(EpicsMotor, "PINXS")
    ys = Cpt(EpicsMotor, "PINXS")
    zs = Cpt(EpicsMotor, "PINZS")
