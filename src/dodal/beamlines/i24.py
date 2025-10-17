from pathlib import PurePath

from ophyd_async.core import AutoIncrementingPathProvider, StaticFilenameProvider

from dodal.common.beamlines.beamline_utils import (
    BL,
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.attenuator.attenuator import EnumFilterAttenuator
from dodal.devices.attenuator.filter_selections import (
    I24_FilterOneSelections,
    I24_FilterTwoSelections,
)
from dodal.devices.hutch_shutter import HutchShutter
from dodal.devices.i24.aperture import Aperture
from dodal.devices.i24.beam_center import DetectorBeamCenter
from dodal.devices.i24.beamstop import Beamstop
from dodal.devices.i24.commissioning_jungfrau import CommissioningJungfrau
from dodal.devices.i24.dcm import DCM
from dodal.devices.i24.dual_backlight import DualBacklight
from dodal.devices.i24.focus_mirrors import FocusMirrorsMode
from dodal.devices.i24.pmac import PMAC
from dodal.devices.i24.vgonio import VerticalGoniometer
from dodal.devices.motors import YZStage
from dodal.devices.oav.oav_detector import OAVBeamCentreFile
from dodal.devices.oav.oav_parameters import OAVConfigBeamCentre
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

ZOOM_PARAMS_FILE = (
    "/dls_sw/i24/software/gda_versions/gda/config/xml/jCameraManZoomLevels.xml"
)
DISPLAY_CONFIG = "/dls_sw/i24/software/gda_versions/var/display.configuration"


BL = get_beamline_name("i24")
set_log_beamline(BL)
set_utils_beamline(BL)

I24_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(TTL_EIGER=1, TTL_PILATUS=2, TTL_FAST_SHUTTER=4),
    sources=ZebraSources(),
)

PREFIX = BeamlinePrefix(BL)


@device_factory()
def attenuator() -> EnumFilterAttenuator:
    """Get a read-only attenuator device for i24, instantiate it if it hasn't already
    been. If this is called when already instantiated in i24, it will return the
    existing object."""
    return EnumFilterAttenuator(
        f"{PREFIX.beamline_prefix}-OP-ATTN-01:",
        filter_selection=(I24_FilterOneSelections, I24_FilterTwoSelections),
    )


@device_factory()
def aperture() -> Aperture:
    """Get the i24 aperture device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return Aperture(
        f"{PREFIX.beamline_prefix}-AL-APTR-01:",
    )


@device_factory()
def beamstop() -> Beamstop:
    """Get the i24 beamstop device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return Beamstop(
        f"{PREFIX.beamline_prefix}-MO-BS-01:",
    )


@device_factory()
def backlight() -> DualBacklight:
    """Get the i24 backlight device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return DualBacklight(
        prefix=PREFIX.beamline_prefix,
    )


@device_factory()
def detector_motion() -> YZStage:
    """Get the i24 detector motion device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return YZStage(
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-01:",
    )


@device_factory()
def dcm() -> DCM:
    """Get the i24 DCM device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return DCM(
        prefix=f"{PREFIX.beamline_prefix}-DI-DCM-01:",
        motion_prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:",
    )


# TODO implement ophyd-async eiger see
# https://github.com/DiamondLightSource/mx-bluesky/issues/62
# @skip_device(lambda: BL == "s24")
# def eiger(
#     wait_for_connection: bool = True,
#     fake_with_ophyd_sim: bool = False,
#     params: DetectorParams | None = None,
# ) -> EigerDetector:
#     """Get the i24 Eiger device, instantiate it if it hasn't already been.
#     If this is called when already instantiated, it will return the existing object.
#     If called with params, will update those params to the Eiger object.
#     """
#
#     def set_params(eiger: EigerDetector):
#         if params is not None:
#             eiger.set_detector_parameters(params)
#
#     return device_instantiation(
#         device_factory=EigerDetector,
#         name="eiger",
#         prefix="-EA-EIGER-01:",
#         wait=wait_for_connection,
#         fake=fake_with_ophyd_sim,
#         post_create=set_params,
#     )


@device_factory()
def pmac() -> PMAC:
    """Get the i24 PMAC device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return PMAC(PREFIX.beamline_prefix)


@device_factory()
def oav() -> OAVBeamCentreFile:
    return OAVBeamCentreFile(
        prefix=f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        config=OAVConfigBeamCentre(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


@device_factory()
def vgonio() -> VerticalGoniometer:
    """Get the i24 vertical goniometer device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return VerticalGoniometer(f"{PREFIX.beamline_prefix}-MO-VGON-01:")


@device_factory()
def zebra() -> Zebra:
    """Get the i24 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i24, it will return the existing object.
    """
    return Zebra(
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:",
        mapping=I24_ZEBRA_MAPPING,
    )


@device_factory()
def shutter() -> HutchShutter:
    """Get the i24 hutch shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated, it will return the existing object.
    """
    return HutchShutter(f"{PREFIX.beamline_prefix}-PS-SHTR-01:")


@device_factory()
def focus_mirrors() -> FocusMirrorsMode:
    """Get the i24 focus mirror devise to find the beam size."""
    return FocusMirrorsMode(f"{PREFIX.beamline_prefix}-OP-MFM-01:")


@device_factory()
def eiger_beam_center() -> DetectorBeamCenter:
    """A device for setting/reading the beamcenter from the eiger on i24."""
    return DetectorBeamCenter(
        f"{PREFIX.beamline_prefix}-EA-EIGER-01:CAM:",
        "eiger_bc",
    )


@device_factory()
def commissioning_jungfrau(
    path_to_dir: str = "/tmp/jf",  # Device factory doesn't allow for required args,
    filename: str = "jf_output",  # but these should be manually entered when commissioning
) -> CommissioningJungfrau:
    """Get the commissionning Jungfrau 9M device, which uses a temporary filewriter
    device in place of Odin while the detector is in commissioning.
    Instantiates the device if it hasn't already been.
    If this is called when already instantiated, it will return the existing object."""

    return CommissioningJungfrau(
        f"{PREFIX.beamline_prefix}-EA-JFRAU-01:",
        f"{PREFIX.beamline_prefix}-JUNGFRAU-META:FD:",
        AutoIncrementingPathProvider(
            StaticFilenameProvider(filename), PurePath(path_to_dir)
        ),
    )
