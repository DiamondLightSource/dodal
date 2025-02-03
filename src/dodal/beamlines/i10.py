"""
I10 has two insertion devices one up(idu) and one down stream(idd).
It is worth noting that the down stream device is slightly longer,
so it can reach Mn edge for linear arbitrary.
 idd == id1,    idu == id2.
"""

from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.current_amplifiers import CurrentAmpDet
from dodal.devices.i10.i10_apple2 import (
    I10Id,
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
from dodal.devices.i10.slits import I10PrimarySlits, I10Slits
from dodal.devices.motors import XYZPositioner
from dodal.devices.pgm import PGM
from dodal.devices.slits import MinimalSlits
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)


LOOK_UPTABLE_DIR = "/dls_sw/i10/software/gda/workspace_git/gda-diamond.git/configurations/i10-shared/lookupTables/"


@device_factory()
def pgm() -> PGM:
    "I10 Plane Grating Monochromator, it can change energy via pgm.energy.set(<energy>)"
    return PGM(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=I10Grating,
        gratingPv="NLINES2",
    )


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


"Rasor devices"


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
def sample_stage() -> XYZPositioner:
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
