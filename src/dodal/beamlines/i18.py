from pathlib import Path

# from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import (
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.devices.common_dcm import BaseDCM, PitchAndRollCrystal, RollCrystal
from dodal.devices.i18.diode import Diode
from dodal.devices.i18.KBMirror import KBMirror
from dodal.devices.i18.table import Table
from dodal.devices.i18.thor_labs_stage import ThorLabsStage
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.tetramm import TetrammDetector
from dodal.devices.undulator import Undulator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name
from ophyd_async.epics.motor import Motor

BL = get_beamline_name("i18")
PREFIX = BeamlinePrefix(BL)
mono_base_pv = f"{PREFIX.beamline_prefix}-MO-DCM-01"
set_log_beamline(BL)
set_utils_beamline(BL)


# Currently we must hard-code the visit, determining the visit at runtime requires
# infrastructure that is still WIP.
# Communication with GDA is also WIP so for now we determine an arbitrary scan number
# locally and write the commissioning directory. The scan number is not guaranteed to
# be unique and the data is at risk - this configuration is for testing only.
set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/dls/i18/data/2025/cm40636-2/bluesky"),
        client=LocalDirectoryServiceClient(),
    )
)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def undulator() -> Undulator:
    return Undulator(f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


# See https://github.com/DiamondLightSource/dodal/issues/1180
@device_factory(skip=True)
def dcm() -> BaseDCM[RollCrystal, PitchAndRollCrystal]:
    # once spacing is added Si111 d-spacing is 3.135 angsterm , and Si311 is 1.637
    # calculations are in gda/config/lookupTables/Si111/eV_Deg_converter.xml
    return BaseDCM(
        prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:",
        xtal_1=RollCrystal,
        xtal_2=PitchAndRollCrystal,
    )

# ID gap [mm]
@device_factory()
def id_gap() -> Motor :
    return Motor(f"{PREFIX.insertion_prefix}-MO-SERVC-01:BLGAPMTR")

# Bragg angle [degrees]
@device_factory()
def dcm_bragg() -> Motor :
    return Motor(f"{mono_base_pv}:BRAGG")

# Perp [mm]
@device_factory()
def dcm_perp() -> Motor :
    return Motor(f"{mono_base_pv}:PERP")

# Energy [KeV]
@device_factory()
def dcm_energy() -> Motor :
    return Motor(f"{mono_base_pv}:ENERGY")

# Crystal1 roll [urad]
@device_factory()
def dcm_crystal1_roll() -> Motor :
    return Motor(f"{mono_base_pv}:XTAL1:ROLL")

# Crystal2 roll [urad]
@device_factory()
def dcm_crystal2_roll() -> Motor :
    return Motor(f"{mono_base_pv}:XTAL2:ROLL")

# Crystal type (Si111, Si311) - read only. Can use ophyd.pv_positioner.PVPositioner (see variant_positioner.py)
@device_factory()
def dcm_crystal() -> Motor :
    return Motor(f"{mono_base_pv}:MP:X:SELECT")

@device_factory()
def s1_slits() -> Slits:
    return Slits(
        f"{PREFIX.beamline_prefix}-AL-SLITS-01:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )

@device_factory()
def s2_slits() -> Slits:
    return Slits(
        f"{PREFIX.beamline_prefix}-AL-SLITS-02:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )

"""
GDA also has motors to control s3 individual blades positions. 
"""
@device_factory()
def s3_slits() -> Slits:
    return Slits(
        f"{PREFIX.beamline_prefix}-AL-SLITS-03:",
        x_centre="X:CENTER",
        y_centre="Y:CENTER",
    )

# PandA IOC needs to be updated to support PVI
"""
@device_factory(skip=True)
def panda1() -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-MO-PANDA-01:",
        path_provider=get_path_provider(),
    )
"""


@device_factory()
def i0() -> TetrammDetector:
    return TetrammDetector(
        f"{PREFIX.beamline_prefix}-DI-XBPM-02:",
        path_provider=get_path_provider(),
        type="Cividec Diamond XBPM",
    )


@device_factory()
def it() -> TetrammDetector:
    return TetrammDetector(
        f"{PREFIX.beamline_prefix}-DI-XBPM-01:",
        path_provider=get_path_provider(),
    )


@device_factory(skip=True)
# VFM uses different IOC than HFM https://github.com/DiamondLightSource/dodal/issues/1009
def vfm() -> KBMirror:
    return KBMirror(f"{PREFIX.beamline_prefix}-OP-KBM-01:VFM:")


@device_factory()
def hfm() -> KBMirror:
    return KBMirror(f"{PREFIX.beamline_prefix}-OP-KBM-01:HFM:")


@device_factory()
def d7diode() -> Diode:
    return Diode(f"{PREFIX.beamline_prefix}-DI-PHDGN-07:")

@device_factory()
def thor_labs_stage() -> ThorLabsStage:
    return ThorLabsStage(f"{PREFIX.beamline_prefix}-MO-TABLE-02:")

# Table1 motors
@device_factory()
def table1() -> Table:
    return Table(f"{PREFIX.beamline_prefix}-MO-TABLE-01:")

@device_factory()
def t1x() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-01:X")

@device_factory()
def t1y() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-01:Y")

@device_factory()
def t1z() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-01:Z")

@device_factory()
def t1theta() -> Motor:
    return Motor(f"{PREFIX.beamline_prefix}-MO-TABLE-01:THETA")
