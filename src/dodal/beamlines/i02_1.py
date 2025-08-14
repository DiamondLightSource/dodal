"""Beamline i02-1 is also known as VMXm, or I02J"""

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    device_instantiation,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.attenuator.attenuator import EnumFilterAttenuator
from dodal.devices.attenuator.filter_selections import (
    I02_1FilterFourSelections,
    I02_1FilterOneSelections,
    I02_1FilterThreeSelections,
    I02_1FilterTwoSelections,
)
from dodal.devices.eiger import EigerDetector
from dodal.devices.i02_1.fast_grid_scan import TwoDFastGridScan
from dodal.devices.i02_1.sample_motors import SampleMotors
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
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
def eiger(mock: bool = False) -> EigerDetector:
    """Get the i02-1 Eiger device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i02-1, it will return the existing object.
    """
    return device_instantiation(
        device_factory=EigerDetector,
        name="eiger",
        prefix=f"{PREFIX.beamline_prefix}-EA-EIGER-01:",
        bl_prefix=False,
        wait=False,
        fake=mock,
    )


@device_factory()
def zebra_fast_grid_scan() -> TwoDFastGridScan:
    """Get the i02-1 zebra_fast_grid_scan device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i02-1, it will return the existing object.
    """
    return TwoDFastGridScan(
        prefix=f"{PREFIX.beamline_prefix}-MO-SAMP-11:FGS:",
        name="zebra_fast_grid_scan",
    )


@device_factory()
def synchrotron() -> Synchrotron:
    """Get the i03 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return Synchrotron("", "synchrotron")


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
