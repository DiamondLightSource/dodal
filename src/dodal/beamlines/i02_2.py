"""Beamline i02-2 is also known as VMXi, or I02I"""

from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.attenuator.attenuator import EnumFilterAttenuator
from dodal.devices.attenuator.filter_selections import (
    I02_2FilterOneSelections,
    I02_2FilterThreeSelections,
    I02_2FilterTwoSelections,
)
from dodal.devices.motors import XYStage
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i02-2")
PREFIX = BeamlinePrefix(BL, suffix="I")
set_log_beamline(BL)
set_utils_beamline(BL)
DAQ_CONFIGURATION_PATH = "/dls_sw/i02-2/software/daq_configuration"


@device_factory()
def synchrotron() -> Synchrotron:
    """Get the i02-2 synchrotron device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i02-2, it will return the existing object.
    """
    return Synchrotron()


@device_factory()
def sample_motors() -> XYStage:
    """Get the i02-2 goniometer device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i02-2, it will return the existing object.
    """
    return XYStage(f"{PREFIX.beamline_prefix}-MO-GONIO-01:SAMPLE:")


@device_factory()
def attenuator() -> EnumFilterAttenuator:
    """Get the i02-2 attenuator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i02-2, it will return the existing object.
    """

    return EnumFilterAttenuator(
        f"{PREFIX.beamline_prefix}-OP-ATTN-01:",
        (
            I02_2FilterOneSelections,
            I02_2FilterTwoSelections,
            I02_2FilterThreeSelections,
        ),
    )
