from pathlib import Path

from ophyd_async.epics.motor import Motor

from dodal.common.beamlines.beamline_utils import device_factory, device_instantiation
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.apple2_undulator import (
    UndulatorGap,
    UndulatorJawPhase,
    UndulatorPhaseAxes,
)
from dodal.devices.i10.i10_apple2 import (
    I10Apple2,
    I10Apple2PGM,
    I10Apple2Pol,
    LinearArbitraryAngle,
)
from dodal.devices.i10.i10_setting_data import I10Grating
from dodal.devices.i10.mirrors import PiezoMirror
from dodal.devices.i10.slits import I10PrimarySlits, I10Slits
from dodal.devices.pgm import PGM
from dodal.devices.slits import MinimalSlits
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)


LOOK_UPTABLE_DIR = "/dls_sw/i10/software/gda/workspace_git/gda-diamond.git/configurations/i10-shared/lookupTables/"
"""
I10 has two insertion devices one up(idu) and one down stream(idd).
It is worth noting that the down stream device is slightly longer,
 so it can reach Mn edge for linear arbitrary.
 idd == id1
 and
 idu == id2.
"""


def idd_gap(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> UndulatorGap:
    return device_instantiation(
        device_factory=UndulatorGap,
        name="idd_gap",
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        bl_prefix=False,
    )


def idd_phase_axes(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> UndulatorPhaseAxes:
    return device_instantiation(
        device_factory=UndulatorPhaseAxes,
        name="idd_phase_axes",
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="RPQ1",
        top_inner="RPQ2",
        btm_inner="RPQ3",
        btm_outer="RPQ4",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        bl_prefix=False,
    )


def idd_jaw(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> UndulatorJawPhase:
    return device_instantiation(
        device_factory=UndulatorJawPhase,
        name="idd_jaw",
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        move_pv="RPQ1",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        bl_prefix=False,
    )


def idu_gap(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> UndulatorGap:
    return device_instantiation(
        device_factory=UndulatorGap,
        name="idu_gap",
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        bl_prefix=False,
    )


def idu_phase_axes(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> UndulatorPhaseAxes:
    return device_instantiation(
        device_factory=UndulatorPhaseAxes,
        name="idu_phase_axes",
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:",
        top_outer="RPQ1",
        top_inner="RPQ2",
        btm_inner="RPQ3",
        btm_outer="RPQ4",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        bl_prefix=False,
    )


def idu_jaw(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> UndulatorJawPhase:
    return device_instantiation(
        device_factory=UndulatorJawPhase,
        name="idu_jaw",
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:",
        move_pv="RPQ1",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        bl_prefix=False,
    )


def pgm(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> PGM:
    return device_instantiation(
        device_factory=PGM,
        name="pgm",
        prefix="-OP-PGM-01:",
        grating=I10Grating,
        gratingPv="NLINES2",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def idu_gap_phase(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> I10Apple2:
    return device_instantiation(
        device_factory=I10Apple2,
        id_gap=idu_gap(wait_for_connection, fake_with_ophyd_sim),
        id_phase=idu_phase_axes(wait_for_connection, fake_with_ophyd_sim),
        id_jaw_phase=idu_jaw(wait_for_connection, fake_with_ophyd_sim),
        energy_gap_table_path=Path(
            LOOK_UPTABLE_DIR + "IDEnergy2GapCalibrations.csv",
        ),
        energy_phase_table_path=Path(
            LOOK_UPTABLE_DIR + "IDEnergy2PhaseCalibrations.csv",
        ),
        source=("Source", "idu"),
        name="idu_gap_phase",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def idd_gap_phase(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> I10Apple2:
    return device_instantiation(
        device_factory=I10Apple2,
        id_gap=idd_gap(wait_for_connection, fake_with_ophyd_sim),
        id_phase=idd_phase_axes(wait_for_connection, fake_with_ophyd_sim),
        id_jaw_phase=idd_jaw(wait_for_connection, fake_with_ophyd_sim),
        energy_gap_table_path=Path(
            LOOK_UPTABLE_DIR + "IDEnergy2GapCalibrations.csv",
        ),
        energy_phase_table_path=Path(
            LOOK_UPTABLE_DIR + "IDEnergy2PhaseCalibrations.csv",
        ),
        source=("Source", "idd"),
        name="idd_gap_phase",
        prefix="",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def idu_pol(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> I10Apple2Pol:
    return device_instantiation(
        device_factory=I10Apple2Pol,
        prefix="",
        id=idu_gap_phase(wait_for_connection, fake_with_ophyd_sim),
        name="idu_pol",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def idd_pol(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> I10Apple2Pol:
    return device_instantiation(
        device_factory=I10Apple2Pol,
        prefix="",
        id=idd_gap_phase(wait_for_connection, fake_with_ophyd_sim),
        name="idd_pol",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def idu(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> I10Apple2PGM:
    return device_instantiation(
        device_factory=I10Apple2PGM,
        prefix="",
        id=idu_gap_phase(wait_for_connection, fake_with_ophyd_sim),
        pgm=pgm(wait_for_connection, fake_with_ophyd_sim),
        name="idu",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def idd(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> I10Apple2PGM:
    return device_instantiation(
        device_factory=I10Apple2PGM,
        prefix="",
        id=idd_gap_phase(wait_for_connection, fake_with_ophyd_sim),
        pgm=pgm(wait_for_connection, fake_with_ophyd_sim),
        name="idd",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def idu_la_angle(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> LinearArbitraryAngle:
    return device_instantiation(
        device_factory=LinearArbitraryAngle,
        prefix="",
        id=idu(wait_for_connection, fake_with_ophyd_sim),
        name="idu_la_angle",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


def idd_la_angle(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> LinearArbitraryAngle:
    return device_instantiation(
        device_factory=LinearArbitraryAngle,
        prefix="",
        id=idu(wait_for_connection, fake_with_ophyd_sim),
        name="idd_la_angle",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@device_factory()
def first_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-COL-01:")


@device_factory()
def switching_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-SWTCH-01:")


@device_factory()
def slit_1() -> I10PrimarySlits:
    return I10PrimarySlits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-01:",
    )


@device_factory()
def slit_2() -> I10Slits:
    return I10Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-02:",
    )


@device_factory()
def slit_3() -> I10Slits:
    return I10Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-03:",
    )


"""Rasor devices"""


@device_factory()
def focusing_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-FOCS-01:")


@device_factory()
def slit_4() -> MinimalSlits:
    return MinimalSlits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-04:",
        x_gap="XSIZE",
        y_gap="YSIZE",
    )


@device_factory()
def slit_5() -> I10Slits:
    return I10Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-05:",
    )


@device_factory()
def slit_6() -> I10Slits:
    return I10Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-06:",
    )


@device_factory()
def d7() -> Motor:
    return Motor(prefix="BL10I-DI-PHDGN-07:Y")
