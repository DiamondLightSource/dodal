from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor


def _suffix_of(type: str, index: int, axis: str) -> str:
    _common_template: str = "-%s-%02d:%s"
    return _common_template % (type, index, axis)


class PvUtils(object):
    @staticmethod
    def centring_motor(axis: str) -> EpicsMotor:
        centring_suffix = _suffix_of("CENT", 1, axis)
        return Cpt(EpicsMotor, suffix=centring_suffix)

    @staticmethod
    def goniometer(index: int, axis: str) -> EpicsMotor:
        gonio_suffix = _suffix_of("GONIO", index, axis)
        return Cpt(EpicsMotor, suffix=gonio_suffix)


class Diffractometer(Device):
    centre_x: EpicsMotor = PvUtils.centring_motor("X")
    centre_y: EpicsMotor = PvUtils.centring_motor("Y")
    centre_z: EpicsMotor = PvUtils.centring_motor("Z")
    detector_distance: EpicsMotor = PvUtils.goniometer(3, "DET")
    omega: EpicsMotor = PvUtils.goniometer(1, "OMEGA")
    phi: EpicsMotor = PvUtils.goniometer(2, "PHI")
    two_theta: EpicsMotor = PvUtils.goniometer(3, "2THETA")
