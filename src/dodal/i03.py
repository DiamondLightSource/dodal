from ophyd import Device

from dodal.devices.aperturescatterguard import ApertureScatterguard
from dodal.devices.backlight import Backlight
from dodal.devices.DCM import DCM
from dodal.devices.detector import DetectorParams
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan_composite import FGSComposite
from dodal.devices.oav.oav_detector import OAV
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("s03")

ACTIVE_DEVICES: dict[str, Device] = {}


def dcm() -> DCM:
    dcm = ACTIVE_DEVICES.get("dcm")
    if dcm is None:
        ACTIVE_DEVICES["dcm"] = DCM(f"{BeamlinePrefix(BL).beamline_prefix}")
        return ACTIVE_DEVICES["dcm"]
    else:
        return dcm


def FGS() -> FGSComposite:
    # fgs, zembra, undulator, synchrotron, slit_aps, smargon
    return FGSComposite(
        insertion_prefix=f"{BeamlinePrefix(BL).insertion_prefix}",
        name="fgs",
        prefix=f"{BeamlinePrefix(BL).beamline_prefix}",
    )


def eiger(params: DetectorParams) -> EigerDetector:
    eiger = ACTIVE_DEVICES.get("eiger")
    if eiger is None:
        ACTIVE_DEVICES["eiger"] = EigerDetector(
            params, prefix=f"{BeamlinePrefix(BL).beamline_prefix}-EA-EIGER-01:"
        )
        return ACTIVE_DEVICES["eiger"]
    else:
        return eiger


def backlight() -> Backlight:
    backlight = ACTIVE_DEVICES.get("backlight")
    if backlight is None:
        ACTIVE_DEVICES["backlight"] = Backlight(
            name="Backlight", prefix=f"{BeamlinePrefix(BL).beamline_prefix}"
        )
        return ACTIVE_DEVICES["backlight"]
    else:
        return backlight


def aperture_scatterguard() -> ApertureScatterguard:
    aperture_scatterguard = ACTIVE_DEVICES.get("aperture_scatterguard")
    if aperture_scatterguard is None:
        ACTIVE_DEVICES["aperture_scatterguard"] = ApertureScatterguard(
            name="ApertureScatterguard", prefix=f"{BeamlinePrefix(BL).beamline_prefix}"
        )
        return ACTIVE_DEVICES["aperture_scatterguard"]
    else:
        return ApertureScatterguard


def oav() -> OAV:
    oav = ACTIVE_DEVICES.get("oav")
    if oav is None:
        ACTIVE_DEVICES["oav"] = OAV(
            name="OAV", prefix=f"{BeamlinePrefix(BL).beamline_prefix}-DI-OAV-01"
        )
        return ACTIVE_DEVICES["oav"]
    else:
        return oav
