from typing import Callable, Dict, List, Optional

from ophyd import Device
from ophyd.sim import make_fake_device

from dodal.devices.aperturescatterguard import AperturePositions, ApertureScatterguard
from dodal.devices.backlight import Backlight
from dodal.devices.DCM import DCM
from dodal.devices.detector import DetectorParams
from dodal.devices.detector_motion import DetectorMotion
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import FastGridScan
from dodal.devices.oav.oav_detector import OAV
from dodal.devices.s4_slit_gaps import S4SlitGaps
from dodal.devices.smargon import Smargon
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.undulator import Undulator
from dodal.devices.zebra import Zebra
from dodal.log import set_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name, skip_device

BL = get_beamline_name("i03")
set_beamline(BL)


ACTIVE_DEVICES: Dict[str, Device] = {}


def clear_devices():
    global ACTIVE_DEVICES
    for d in list(ACTIVE_DEVICES):
        del ACTIVE_DEVICES[d]


def clear_device(name: str):
    global ACTIVE_DEVICES
    del ACTIVE_DEVICES[name]


def list_active_devices() -> List[str]:
    global ACTIVE_DEVICES
    return list(ACTIVE_DEVICES.keys())


def active_device_is_same_type(active_device, device):
    return type(active_device) == device


@skip_device()
def device_instantiation(
    device: Callable,
    name: str,
    prefix: str,
    wait: bool,
    fake: bool,
    post_create: Optional[Callable] = None,
    bl_prefix: bool = True,
) -> Device:
    active_device = ACTIVE_DEVICES.get(name)
    if fake:
        device = make_fake_device(device)
    if active_device is None:
        ACTIVE_DEVICES[name] = device(
            name=name,
            prefix=f"{(BeamlinePrefix(BL).beamline_prefix)}{prefix}"
            if bl_prefix
            else prefix,
        )
        if wait:
            ACTIVE_DEVICES[name].wait_for_connection()
    else:
        if not active_device_is_same_type(active_device, device):
            raise TypeError(
                f"Can't instantiate device of type {type(active_device)} with the same "
                f"name as an existing device. Device name '{name}' already used for "
                f"a(n) {device}."
            )
    if post_create:
        post_create(ACTIVE_DEVICES[name])
    return ACTIVE_DEVICES[name]


@skip_device(lambda: BL == "s03")
def dcm(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> DCM:
    """Get the i03 DCM device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        device=DCM,
        name="dcm",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def aperture_scatterguard(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
    aperture_positions: Optional[AperturePositions] = None,
) -> ApertureScatterguard:
    """Get the i03 aperture and scatterguard device, instantiate it if it hasn't already
    been. If this is called when already instantiated in i03, it will return the existing
    object. If aperture_positions is specified, it will update them.
    """

    def load_positions(a_s: ApertureScatterguard):
        if aperture_positions is not None:
            a_s.load_aperture_positions(aperture_positions)

    return device_instantiation(
        device=ApertureScatterguard,
        name="aperture_scatterguard",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        post_create=load_positions,
    )


def backlight(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Backlight:
    """Get the i03 backlight device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        device=Backlight,
        name="backlight",
        prefix="-EA-BL-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s03")
def detector_motion(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> DetectorMotion:
    """Get the i03 detector motion device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        device=DetectorMotion,
        name="detector_motion",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s03")
def eiger(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
    params: Optional[DetectorParams] = None,
) -> EigerDetector:
    """Get the i03 Eiger device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
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


def fast_grid_scan(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> FastGridScan:
    """Get the i03 fast_grid_scan device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        device=FastGridScan,
        name="fast_grid_scan",
        prefix="-MO-SGON-01:FGS:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s03")
def oav(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> OAV:
    """Get the i03 OAV device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        OAV,
        "oav",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def smargon(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Smargon:
    """Get the i03 Smargon device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Smargon,
        "smargon",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def s4_slit_gaps(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> S4SlitGaps:
    """Get the i03 s4_slit_gaps device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        S4SlitGaps,
        "s4_slit_gaps",
        "-AL-SLITS-04:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == "s03")
def synchrotron(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Synchrotron:
    """Get the i03 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Synchrotron,
        "synchrotron",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
    )


def undulator(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Undulator:
    """Get the i03 undulator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Undulator,
        "undulator",
        f"{BeamlinePrefix(BL).insertion_prefix}-MO-SERVC-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
    )


def zebra(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Zebra:
    """Get the i03 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Zebra,
        "zebra",
        "-EA-ZEBRA-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
