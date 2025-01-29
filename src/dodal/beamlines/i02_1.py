"""Beamline i02-1 is also known as VMXm, or I02J"""

from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_parameters import get_beamline_parameters
from dodal.common.beamlines.beamline_utils import (
    device_factory,
    device_instantiation,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.udc_directory_provider import PandASubpathProvider
from dodal.devices.aperturescatterguard import (
    AperturePosition,
    ApertureScatterguard,
    load_positions_from_beamline_parameters,
)
from dodal.devices.attenuator.attenuator import (
    BinaryFilterAttenuator,
    EnumFilterAttenuator,
)
from dodal.devices.attenuator.filter_selections import (
    I02_1FilterFourSelections,
    I02_1FilterOneSelections,
    I02_1FilterThreeSelections,
    I02_1FilterTwoSelections,
)
from dodal.devices.cryostream import CryoStream
from dodal.devices.detector.detector_motion import DetectorMotion
from dodal.devices.diamond_filter import DiamondFilter, I03Filters
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import PandAFastGridScan, ZebraFastGridScan
from dodal.devices.flux import Flux
from dodal.devices.focusing_mirror import FocusingMirrorWithStripes, MirrorVoltages
from dodal.devices.i02_1.backlight import Backlight
from dodal.devices.i02_1.eiger import VMXMEiger
from dodal.devices.i02_1.sample_motors import SampleMotors
from dodal.devices.i03.beamstop import Beamstop
from dodal.devices.i24.dcm import DCM
from dodal.devices.motors import XYZPositioner
from dodal.devices.oav.oav_detector import OAV
from dodal.devices.oav.oav_parameters import OAVConfig
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.qbpm import QBPM
from dodal.devices.robot import BartRobot
from dodal.devices.s4_slit_gaps import S4SlitGaps
from dodal.devices.smargon import Smargon
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.thawer import Thawer
from dodal.devices.undulator import Undulator
from dodal.devices.undulator_dcm import UndulatorDCM
from dodal.devices.webcam import Webcam
from dodal.devices.xbpm_feedback import XBPMFeedback
from dodal.devices.xspress3.xspress3 import Xspress3
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.devices.zebra.zebra_controlled_shutter import ZebraShutter
from dodal.devices.zocalo import ZocaloResults
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i02-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)
DAQ_CONFIGURATION_PATH = "/dls_sw/i02-1/software/daq_configuration"

I02_1_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(
        TTL_EIGER=4, TTL_XSPRESS3=3, TTL_FAST_SHUTTER=1, TTL_PILATUS=2
    ),
    sources=ZebraSources(),
)


@device_factory()
def attenuator() -> EnumFilterAttenuator:
    """Get the i02-1 attenuator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i02-1, it will return the existing object.
    """

    return EnumFilterAttenuator(
        f"{PREFIX.beamline_prefix}-OP-ATTN-01:",
        (
            I02_1FilterOneSelections,
            I02_1FilterTwoSelections,
            I02_1FilterThreeSelections,
            I02_1FilterFourSelections,
        ),
    )


@device_factory()
def backlight() -> Backlight:
    """Get the i02-1 backlight device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i02-1, it will return the existing object.
    """
    return Backlight(
        prefix=PREFIX.beamline_prefix,
        name="backlight",
    )


@device_factory()
def eiger(mock: bool = False) -> VMXMEiger:
    """Get the i02-1 Eiger device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i02-1, it will return the existing object.
    """
    return device_instantiation(
        device_factory=VMXMEiger,
        name="eiger",
        prefix="-EA-EIGER-01:",
        wait=False,
        fake=mock,
    )


# FGS device looks quite different on vmxm - need a new device
# @device_factory()
# def zebra_fast_grid_scan() -> ZebraFastGridScan:
#     """Get the i02-1 zebra_fast_grid_scan device, instantiate it if it hasn't already been.
#     If this is called when already instantiated in i02-1, it will return the existing object.
#     """
#     return ZebraFastGridScan(
#         prefix=f"{PREFIX.beamline_prefix}-MO-SGON-01:",
#         name="zebra_fast_grid_scan",
#     )


@device_factory()
def synchrotron() -> Synchrotron:
    """Get the i03 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Synchrotron("", "synchrotron")


# Check with scientists to what they actually want to do with their xbpm feedback - do they even need it in their FGS?
# @device_factory()
# def xbpm_feedback() -> XBPMFeedback:
#     """Get the i03 XBPM feeback device, instantiate it if it hasn't already been.
#     If this is called when already instantiated in i03, it will return the existing object.
#     """
#     return XBPMFeedback(
#         PREFIX.beamline_prefix,
#         "xbpm_feedback",
#     )


@device_factory()
def zebra() -> Zebra:
    """Get the i03 zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Zebra(
        name="zebra",
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:",
        mapping=I02_1_ZEBRA_MAPPING,
    )


@device_factory()
def zocalo() -> ZocaloResults:
    """Get the i03 ZocaloResults device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return ZocaloResults(
        name="zocalo",
        prefix=PREFIX.beamline_prefix,
    )


@device_factory()
def goniometer() -> SampleMotors:
    """Get the i02-1 goniometer device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return SampleMotors(f"{PREFIX.beamline_prefix}-MO-SAMP-01:", "goniometer")


@device_factory()
def undulator(daq_configuration_path: str | None = None) -> Undulator:
    """Get the i03 undulator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Undulator(
        f"{BeamlinePrefix(BL).insertion_prefix}-MO-SERVC-01:",
        name="undulator",
        # evaluate here not as parameter default to enable post-import mocking
        id_gap_lookup_table_path=f"{daq_configuration_path or DAQ_CONFIGURATION_PATH}/lookup/BeamLine_Undulator_toGap.txt",
    )


# Need to reconcise with other DCMS: https://github.com/DiamondLightSource/dodal/issues/592
# @device_factory()
# def dcm() -> DCM:
#     """Get the i03 DCM device, instantiate it if it hasn't already been.
#     If this is called when already instantiated in i03, it will return the existing object.
#     """
#     return DCM(
#         f"{PREFIX.beamline_prefix}",
#         "dcm",
#     )
