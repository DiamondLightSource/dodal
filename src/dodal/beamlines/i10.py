"""
note:
    I10 has two insertion devices one up(idu) and one down stream(idd).
    It is worth noting that the downstream device is slightly longer,
    so it can reach Mn edge for linear arbitrary.
    idd == id1,    idu == id2.
"""

from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.current_amplifiers import CurrentAmpDet
from dodal.devices.i10 import (
    I10Diagnostic,
    I10Diagnostic5ADet,
    I10Slits,
    I10SlitsDrainCurrent,
    PiezoMirror,
)
from dodal.devices.i10.diagnostics import I10Diagnostic, I10Diagnostic5ADet
from dodal.devices.i10.rasor.rasor_current_amp import RasorFemto, RasorSR570
from dodal.devices.i10.rasor.rasor_motors import (
    DetSlits,
    Diffractometer,
    PaStage,
)
from dodal.devices.i10.rasor.rasor_scaler_cards import RasorScalerCard1
from dodal.devices.motors import XYStage, XYZStage
from dodal.devices.temperture_controller import (
    Lakeshore340,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)

"""Mirrors"""


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
def pin_hole() -> XYStage:
    return XYStage(prefix="ME01D-EA-PINH-01:")


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
def sample_stage() -> XYZStage:
    return XYZStage(prefix="ME01D-MO-CRYO-01:")


@device_factory()
def rasor_temperature_controller() -> Lakeshore340:
    return Lakeshore340(
        prefix="ME01D-EA-TCTRL-01:",
    )


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
