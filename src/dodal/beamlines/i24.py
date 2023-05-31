from typing import Optional

from dodal.beamlines.beamline_utils import BL, device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.backlight import Backlight
from dodal.devices.DCM import DCM
from dodal.devices.detector import DetectorParams
from dodal.devices.detector_motion import DetectorMotion
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import FastGridScan
from dodal.devices.i24.i24_vgonio import VGonio
from dodal.devices.oav.oav_detector import OAV
from dodal.devices.s4_slit_gaps import S4SlitGaps
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.undulator import Undulator
from dodal.devices.zebra import Zebra
from dodal.log import set_beamline
from dodal.utils import get_beamline_name, skip_device

BL = get_beamline_name("s24")
set_beamline(BL)
set_utils_beamline(BL)


def backlight(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Backlight:
    """Get the i03 backlight device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        device=Backlight,
        name="backlight",
        prefix="-MO-BL-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s24")
def eiger(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
    params: Optional[DetectorParams] = None,
) -> EigerDetector:
    """Get the i24 Eiger device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    If called with params, will update those params to the Eiger object.
    """

    def set_params(eiger: EigerDetector):
        if params is not None:
            eiger.set_detector_parameters(params)

    return device_instantiation(
        device=EigerDetector,
        name="eiger",
        prefix="-EA-EIGER-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        post_create=set_params,
    )


@skip_device(lambda: BL == "s24")
def vgonio(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> OAV:
    """Get the i24 vgonio device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return device_instantiation(
        VGonio,
        "vgonio",
        "-MO-VGON-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
