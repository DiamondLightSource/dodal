from pathlib import Path

from dodal.common.beamlines.beamline_utils import device_factory, device_instantiation
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.apple2_undulator import (
    UndulatorGap,
    UndulatorJawPhase,
    UndulatorPhaseAxes,
)
from dodal.devices.current_amplifiers import CurrentAmpDet
from dodal.devices.i10.diagnostics import I10Diagnostic, I10Diagnostic5ADet
from dodal.devices.i10.i10_apple2 import (
    I10Apple2,
    I10Apple2PGM,
    I10Apple2Pol,
    LinearArbitraryAngle,
)
from dodal.devices.i10.i10_setting_data import I10Grating
from dodal.devices.i10.mirrors import PiezoMirror
from dodal.devices.i10.rasor.rasor_current_amp import RasorFemto, RasorSR570
from dodal.devices.i10.rasor.rasor_motors import (
    DetSlits,
    Diffractometer,
    PaStage,
    PinHole,
)
from dodal.devices.i10.rasor.rasor_scaler_cards import RasorScalerCard1
from dodal.devices.i10.slits import I10Slits, I10SlitsDrainCurrent
from dodal.devices.motors import XYZPositioner
from dodal.devices.pgm import PGM
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


"""Mirrors"""


@device_factory()
def first_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-COL-01:")


@device_factory()
def switching_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-SWTCH-01:")


@device_factory()
def focusing_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-FOCS-01:")


"""Optic slits"""


@device_factory()
def slits() -> I10Slits:
    return I10Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-")


@device_factory()
def slits_current() -> I10SlitsDrainCurrent:
    return I10SlitsDrainCurrent(prefix=f"{PREFIX.beamline_prefix}-")


"""Diagnostics"""


@device_factory()
def diagnostics() -> I10Diagnostic:
    return I10Diagnostic(
        prefix=f"{PREFIX.beamline_prefix}-DI-",
    )


@device_factory()
def d5a_det() -> I10Diagnostic5ADet:
    return I10Diagnostic5ADet(prefix=f"{PREFIX.beamline_prefix}-DI-")


"""Rasor devices"""


@device_factory()
def pin_hole() -> PinHole:
    return PinHole(prefix="ME01D-EA-PINH-01:")


@device_factory()
def det_slits() -> DetSlits:
    return DetSlits(prefix="ME01D-MO-APTR-0")


@device_factory()
def diffractometer() -> Diffractometer:
    return Diffractometer(prefix="ME01D-MO-DIFF-01:")


@device_factory()
def pa_stage() -> PaStage:
    return PaStage(prefix="ME01D-MO-POLAN-01:")


@device_factory()
def simple_stage() -> XYZPositioner:
    return XYZPositioner(prefix="ME01D-MO-CRYO-01:")


@device_factory()
def rasor_femto() -> RasorFemto:
    return RasorFemto(
        prefix="ME01D-EA-IAMP",
    )


@device_factory()
def rasor_det_scalers() -> RasorScalerCard1:
    return RasorScalerCard1(prefix="ME01D-EA-SCLR-01:SCALER1")


@device_factory()
def rasor_sr570() -> RasorSR570:
    return RasorSR570(
        prefix="ME01D-EA-IAMP",
    )


@device_factory()
def rasor_sr570_pa_scaler_det() -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=rasor_sr570().ca1,
        counter=rasor_det_scalers().det,
    )


@device_factory()
def rasor_femto_pa_scaler_det() -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=rasor_femto().ca1,
        counter=rasor_det_scalers().det,
    )


@device_factory()
def rasor_sr570_fluo_scaler_det() -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=rasor_sr570().ca2,
        counter=rasor_det_scalers().fluo,
    )


@device_factory()
def rasor_femto_fluo_scaler_det() -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=rasor_femto().ca2,
        counter=rasor_det_scalers().fluo,
    )


@device_factory()
def rasor_sr570_drain_scaler_det() -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=rasor_sr570().ca3,
        counter=rasor_det_scalers().drain,
    )


@device_factory()
def rasor_femto_drain_scaler_det() -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=rasor_femto().ca3,
        counter=rasor_det_scalers().drain,
    )
