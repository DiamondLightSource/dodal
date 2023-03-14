from dodal.devices.aperture import Aperture
from dodal.devices.backlight import Backlight
from dodal.devices.DCM import DCM
from dodal.devices.detector import DetectorParams
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan_composite import FGSComposite
from dodal.devices.oav.zoom_controller import OAV
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("s03")


def dcm() -> DCM:
    return DCM(f"{BeamlinePrefix(BL).beamline_prefix}")


def FGS() -> FGSComposite:
    # fgs, zembra, undulator, synchrotron, slit_aps, smargon
    return FGSComposite(
        insertion_prefix=f"{BeamlinePrefix(BL).insertion_prefix}",
        name="fgs",
        prefix=f"{BeamlinePrefix(BL).beamline_prefix}",
    )


def eiger(params: DetectorParams) -> EigerDetector:
    return EigerDetector(
        params, prefix=f"{BeamlinePrefix(BL).beamline_prefix}-EA-EIGER-01:"
    )


def backlight() -> Backlight:
    return Backlight(name="Backlight", prefix=f"{BeamlinePrefix(BL).beamline_prefix}")


def aperture() -> Aperture:
    return Aperture(
        name="Aperture", prefix=f"{BeamlinePrefix(BL).beamline_prefix}-MO-MAPT-01:"
    )


def oav() -> OAV:
    return OAV(name="OAV", prefix=f"{BeamlinePrefix(BL).beamline_prefix}-DI-OAV-01")
