from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor


class Diffractometer(Device):
    def suffix_of(type: str, axis: str, index: int) -> str:
        _common_template: str = "-%s-%02d:%s"
        return _common_template % (type, axis, index)

    def centring_motor(axis: str) -> EpicsMotor:
        centring_suffix = Diffractometer.suffix_of("CENT", axis, 1)
        return Cpt(EpicsMotor, suffix=centring_suffix)

    def goniometer(axis: str, index: int) -> EpicsMotor:
        gonio_suffix = Diffractometer.suffix_of("GONIO", axis, index)
        return Cpt(EpicsMotor, suffix=gonio_suffix)

    centre_x: EpicsMotor = centring_motor("X")
    centre_y: EpicsMotor = centring_motor("Y")
    centre_z: EpicsMotor = centring_motor("Z")
    detector_distance: EpicsMotor = goniometer("DET", 3)
    omega: EpicsMotor = goniometer("OMEGA", 1)
    phi: EpicsMotor = goniometer("PHI", 2)
    two_theta: EpicsMotor = goniometer("2THETA", 3)
