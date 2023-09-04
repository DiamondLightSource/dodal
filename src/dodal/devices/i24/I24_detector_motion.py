from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor


class DetectorMotion(Device):
    """Physical motion for detector travel"""

    y: EpicsMotor = Cpt(EpicsMotor, "Y")  # Vertical
    z: EpicsMotor = Cpt(EpicsMotor, "Z")  # Beam
