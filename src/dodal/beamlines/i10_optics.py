"""
note:
    I10 has two insertion devices one up(idu) and one down stream(idd).
    It is worth noting that the downstream device is slightly longer,
    so it can reach Mn edge for linear arbitrary.
    idd == id1,    idu == id2.
"""

from daq_config_server.client import ConfigServer

from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i10 import (
    I10SharedDiagnostic,
    I10SharedSlits,
    I10SlitsSharedDrainCurrent,
    PiezoMirror,
)
from dodal.devices.i10.i10_apple2 import (
    I10Id,
)

# Imports taken from i10 while we work out how to deal with split end stations
from dodal.devices.i10.i10_setting_data import I10Grating
from dodal.devices.pgm import PGM
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)

LOOK_UPTABLE_DIR = "/dls_sw/i10/software/blueapi/scratch/i10-config/lookupTables/"

"""Mirrors"""


@device_factory()
def first_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-COL-01:")


@device_factory()
def pgm() -> PGM:
    "I10 Plane Grating Monochromator, it can change energy via pgm.energy.set(<energy>)"
    return PGM(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=I10Grating,
        gratingPv="NLINES2",
    )


@device_factory()
def switching_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-SWTCH-01:")


I10_CONF_CLIENT = ConfigServer(url="https://daq-config.diamond.ac.uk")


@device_factory()
def idd() -> I10Id:
    """i10 downstream insertion device:
    id.energy.set(<energy>) to change beamline energy.
    id.energy.energy_offset.set(<off_set>) to change id energy offset relative to pgm.
    id.pol.set(<polarisation>) to change polarisation.
    id.laa.set(<linear polarisation angle>) to change polarisation angle, must be in LA mode.
    """
    return I10Id(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        pgm=pgm(),
        look_up_table_dir=LOOK_UPTABLE_DIR,
        source=("Source", "idd"),
        config_client=I10_CONF_CLIENT,
    )


@device_factory()
def idu() -> I10Id:
    """i10 upstream insertion device:
    id.energy.set(<energy>) to change beamline energy.
    id.energy.energy_offset.set(<off_set>) to change id energy offset relative to pgm.
    id.pol.set(<polarisation>) to change polarisation.
    id.laa.set(<linear polarisation angle>) to change polarisation angle, must be in LA mode.
    """
    return I10Id(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:",
        pgm=pgm(),
        look_up_table_dir=LOOK_UPTABLE_DIR,
        source=("Source", "idu"),
        config_client=I10_CONF_CLIENT,
    )


"""Slits"""


@device_factory()
def optics_slits() -> I10SharedSlits:
    return I10SharedSlits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-")


"""Diagnostics"""


@device_factory()
def optics_diagnostics() -> I10SharedDiagnostic:
    return I10SharedDiagnostic(
        prefix=f"{PREFIX.beamline_prefix}-DI-",
    )


@device_factory()
def optics_slits_current() -> I10SlitsSharedDrainCurrent:
    return I10SlitsSharedDrainCurrent(prefix=f"{PREFIX.beamline_prefix}-")
