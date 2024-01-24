from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor


class DetectorMotion(Device):
    """Physical motion for detector travel"""

    y = Cpt(EpicsMotor, "Y")  # Vertical
    z = Cpt(EpicsMotor, "Z")  # Beam
