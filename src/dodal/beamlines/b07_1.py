from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.b07_1 import (
    B07CGrating,
    ChannelCutMonochromator,
    ChannelCutMonochromatorPositions,
)
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO
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
    return PGM(prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:", grating=B07CGrating)


@device_factory()
def ccmc() -> ChannelCutMonochromator:
    return ChannelCutMonochromator(
        prefix=f"{PREFIX.beamline_prefix}-OP-CCM-01:",
        positions=ChannelCutMonochromatorPositions,
    )


@device_factory()
def analyser_driver() -> SpecsAnalyserDriverIO:
    energy_sources = {
        "source1": pgm().energy.user_readback,
        "source2": ccmc().energy_in_ev,
    }
    return SpecsAnalyserDriverIO(
        f"{PREFIX.beamline_prefix}-EA-DET-01:CAM:", energy_sources
    )
