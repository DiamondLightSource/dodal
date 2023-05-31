from ophyd import Component as Cpt
from ophyd import EpicsMotor
from ophyd.epics_motor import MotorBundle


class VGonio(MotorBundle):
    x: EpicsMotor = Cpt(EpicsMotor, "-MO-VGON-01:PINX")
    z: EpicsMotor = Cpt(EpicsMotor, "-MO-VGON-01:PINZ")
    yh: EpicsMotor = Cpt(EpicsMotor, "-MO-VGON-01:PINYH")
    omega: EpicsMotor = Cpt(EpicsMotor, "-MO-VGON-01:OMEGA")
    kappa: EpicsMotor = Cpt(EpicsMotor, "-MO-VGON-01:KAPPA")
    phi: EpicsMotor = Cpt(EpicsMotor, "-MO-VGON-01:PHI")

    # Real motors
    xs: EpicsMotor = Cpt(EpicsMotor, "-MO-VGON-01:PINXS")
    ys: EpicsMotor = Cpt(EpicsMotor, "-MO-VGON-01:PINXS")
    zs: EpicsMotor = Cpt(EpicsMotor, "-MO-VGON-01:PINZS")
