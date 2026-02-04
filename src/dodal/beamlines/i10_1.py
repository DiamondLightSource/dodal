from dodal.beamlines.i10_shared import devices as i10_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i10 import I10JDiagnostic, I10JSlits, PiezoMirror
from dodal.devices.beamlines.i10_1 import (
    ElectromagnetMagnetField,
    ElectromagnetStage,
    I10JScalerCard,
)
from dodal.devices.current_amplifiers import SR570, CurrentAmpDet
from dodal.devices.temperture_controller.lakeshore.lakeshore import Lakeshore336
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10-1")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix("i10", "J")
devices = DeviceManager()
devices.include(i10_shared_devices)

"""I10J Beamline Devices"""


@devices.factory()
def mirror6_sr570() -> SR570:
    return SR570(prefix=f"{PREFIX.beamline_prefix}-DI-IAMP-07:")


@devices.factory()
def slits() -> I10JSlits:
    return I10JSlits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-")


@devices.factory()
def diagnostic() -> I10JDiagnostic:
    return I10JDiagnostic(
        prefix=f"{PREFIX.beamline_prefix}-DI-",
    )


@devices.factory()
def focusing_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-FOCA-01:")


"""I10J Electromagnet Devices"""


@devices.factory()
def electromagnet_field() -> ElectromagnetMagnetField:
    return ElectromagnetMagnetField(
        prefix=f"{PREFIX.beamline_prefix}-EA-MAGC-01:",
    )


@devices.factory()
def electromagnet_stage() -> ElectromagnetStage:
    return ElectromagnetStage(
        prefix=f"{PREFIX.beamline_prefix}-MO-CRYO-01:",
    )


"""I10J Electromagnet Measurement Devices"""


@devices.factory()
def electromagnet_scaler_card() -> I10JScalerCard:
    return I10JScalerCard(
        prefix=f"{PREFIX.beamline_prefix}-EA-SCLR-02:SCALERJ3",
    )


@devices.factory()
def em_sr570_tey() -> SR570:
    return SR570(
        prefix=f"{PREFIX.beamline_prefix}-DI-IAMP-08:",
    )


@devices.factory()
def em_sr570_fy() -> SR570:
    return SR570(
        prefix=f"{PREFIX.beamline_prefix}-DI-IAMP-09:",
    )


@devices.factory()
def electromagnet_sr570_scaler_monitor(
    mirror6_sr570: SR570,
    electromagnet_scaler_card: I10JScalerCard,
) -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=mirror6_sr570, counter=electromagnet_scaler_card.mon
    )


@devices.factory()
def electromagnet_sr570_scaler_tey(
    em_sr570_tey: SR570,
    electromagnet_scaler_card: I10JScalerCard,
) -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=em_sr570_tey,
        counter=electromagnet_scaler_card.tey,
    )


@devices.factory()
def electromagnet_sr570_scaler_fy(
    em_sr570_fy: SR570,
    electromagnet_scaler_card: I10JScalerCard,
) -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=em_sr570_fy,
        counter=electromagnet_scaler_card.fy,
    )


@devices.factory()
def em_temperature_controller() -> Lakeshore336:
    return Lakeshore336(
        prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-41:",
    )
