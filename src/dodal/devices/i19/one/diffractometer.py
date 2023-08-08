from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor


def _suffix_of(type: str, axis: str, index: int) -> str:
    _common_template: str = "-%s-%02d:%s"
    return _common_template % (type, axis, index)


class PvUtils(object):
    @staticmethod
    def centring_motor(axis: str) -> EpicsMotor:
        centring_suffix = _suffix_of("CENT", axis, 1)
        return Cpt(EpicsMotor, suffix=centring_suffix)

    @staticmethod
    def goniometer(axis: str, index: int) -> EpicsMotor:
        gonio_suffix = _suffix_of("GONIO", axis, index)
        return Cpt(EpicsMotor, suffix=gonio_suffix)


class Diffractometer(Device):
    centre_x: EpicsMotor = PvUtils.centring_motor("X")
    centre_y: EpicsMotor = PvUtils.centring_motor("Y")
    centre_z: EpicsMotor = PvUtils.centring_motor("Z")
    detector_distance: EpicsMotor = PvUtils.goniometer("DET", 3)
    omega: EpicsMotor = PvUtils.goniometer("OMEGA", 1)
    phi: EpicsMotor = PvUtils.goniometer("PHI", 2)
    two_theta: EpicsMotor = PvUtils.goniometer("2THETA", 3)
