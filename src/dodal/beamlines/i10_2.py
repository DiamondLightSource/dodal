"""
Generated on: 2026-01-09 14:17:48
Beamline: i10

note:

"""

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.current_amplifiers import CurrentAmpDet
from dodal.devices.i10 import PiezoMirror
from dodal.devices.i10.rasor.rasor_current_amp import RasorSR570
from dodal.devices.i10.rasor.rasor_scaler_cards import RasorScalerCard1
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

devices = DeviceManager()
BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)


""" Mirrors """


@devices.factory()
def focusing_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-FOCS-01:")


@devices.factory()
def switching_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-SWTCH-01:")


""" Rasor Detectors """


@devices.factory(mock=True)
def rasor_det_scalers() -> RasorScalerCard1:
    return RasorScalerCard1(prefix="ME01D-EA-SCLR-01:SCALER1")


@devices.factory(mock=True)
def rasor_sr570() -> RasorSR570:
    return RasorSR570(prefix="ME01D-EA-IAMP")


@devices.factory(mock=True, skip=True)
def rasor_sr570_pa_scaler_det() -> CurrentAmpDet:
    return CurrentAmpDet(current_amp=rasor_sr570().ca1, counter=rasor_det_scalers().det)
