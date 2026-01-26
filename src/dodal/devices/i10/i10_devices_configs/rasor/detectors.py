from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.current_amplifiers import CurrentAmpDet
from dodal.devices.i10.rasor.rasor_current_amp import RasorFemto, RasorSR570
from dodal.devices.i10.rasor.rasor_scaler_cards import RasorScalerCard1
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)
devices_femto = DeviceManager()
devices_sr570 = DeviceManager()
devices_scaler_cards = DeviceManager()
devices_sr570_det = DeviceManager()
devices_femto_det = DeviceManager()


@devices_femto.factory()
def rasor_femto() -> RasorFemto:
    return RasorFemto(
        prefix="ME01D-EA-IAMP",
    )


@devices_scaler_cards.factory()
def rasor_det_scalers() -> RasorScalerCard1:
    return RasorScalerCard1(prefix="ME01D-EA-SCLR-01:SCALER1")


@devices_sr570.factory()
def rasor_sr570() -> RasorSR570:
    return RasorSR570(
        prefix="ME01D-EA-IAMP",
    )


@devices_sr570_det.factory()
def rasor_sr570_pa_scaler_det(
    rasor_sr570: RasorSR570, rasor_det_scalers: RasorScalerCard1
) -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=rasor_sr570.ca1,
        counter=rasor_det_scalers.det,
    )


@devices_femto_det.factory()
def rasor_femto_pa_scaler_det(
    rasor_femto: RasorFemto, rasor_det_scalers: RasorScalerCard1
) -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=rasor_femto.ca1,
        counter=rasor_det_scalers.det,
    )


@devices_sr570_det.factory()
def rasor_sr570_fluo_scaler_det(
    rasor_sr570: RasorSR570, rasor_det_scalers: RasorScalerCard1
) -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=rasor_sr570.ca2,
        counter=rasor_det_scalers.fluo,
    )


@devices_femto_det.factory()
def rasor_femto_fluo_scaler_det(
    rasor_femto: RasorFemto, rasor_det_scalers: RasorScalerCard1
) -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=rasor_femto.ca2,
        counter=rasor_det_scalers.fluo,
    )


@devices_sr570_det.factory()
def rasor_sr570_drain_scaler_det(
    rasor_sr570: RasorSR570, rasor_det_scalers: RasorScalerCard1
) -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=rasor_sr570.ca3,
        counter=rasor_det_scalers.drain,
    )


@devices_femto_det.factory()
def rasor_femto_drain_scaler_det(
    rasor_femto: RasorFemto, rasor_det_scalers: RasorScalerCard1
) -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=rasor_femto.ca3,
        counter=rasor_det_scalers.drain,
    )
