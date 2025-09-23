from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.b07 import PsuMode
from dodal.devices.b07_1 import (
    ChannelCutMonochromator,
    Grating,
    LensMode,
)
from dodal.devices.electron_analyser import EnergySource
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.pgm import PGM
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("b07-1")
PREFIX = BeamlinePrefix(BL, suffix="C")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def pgm() -> PGM:
    return PGM(prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:", grating=Grating)


# Connect will work again after this work completed
# https://jira.diamond.ac.uk/browse/B07-1104
@device_factory()
def ccmc() -> ChannelCutMonochromator:
    return ChannelCutMonochromator(prefix=f"{PREFIX.beamline_prefix}-OP-CCM-01:")


@device_factory()
def energy_source() -> EnergySource:
    return EnergySource(pgm().energy.user_readback)


@device_factory()
def analyser() -> SpecsDetector[LensMode, PsuMode]:
    return SpecsDetector[LensMode, PsuMode](
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-01:CAM:",
        lens_mode_type=LensMode,
        psu_mode_type=PsuMode,
        energy_source=energy_source(),
    )
