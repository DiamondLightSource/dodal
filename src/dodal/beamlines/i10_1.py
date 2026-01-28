from dodal.beamlines.i10_shared import devices as i10_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.current_amplifiers.current_amplifier_detector import CurrentAmpDet
from dodal.devices.i10 import I10JDiagnostic, I10JSlits, PiezoMirror
from dodal.devices.i10_1 import (
    I10JSR570,
    ElectromagnetMagnetField,
    ElectromagnetScalerCard1,
    ElectromagnetSR570,
    ElectromagnetStage,
)
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
def mirror6_sr570() -> I10JSR570:
    return I10JSR570(
        prefix=f"{PREFIX.beamline_prefix}-DI-IAMP",
    )


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
def electromagnet_scaler_card() -> ElectromagnetScalerCard1:
    return ElectromagnetScalerCard1(
        prefix=f"{PREFIX.beamline_prefix}-EA-SCLR-02:SCALERJ3",
    )


@devices.factory()
def electromagnet_sr570() -> ElectromagnetSR570:
    return ElectromagnetSR570(
        prefix=f"{PREFIX.beamline_prefix}-DI-IAMP",
    )


@devices.factory()
def electromagnet_sr570_scaler_monitor(
    mirror6_sr570: I10JSR570,
    electromagnet_scaler_card: ElectromagnetScalerCard1,
) -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=mirror6_sr570.ca1, counter=electromagnet_scaler_card.mon
    )


@devices.factory()
def electromagnet_sr570_scaler_tey(
    electromagnet_sr570: ElectromagnetSR570,
    electromagnet_scaler_card: ElectromagnetScalerCard1,
) -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=electromagnet_sr570.ca1,
        counter=electromagnet_scaler_card.tey,
    )


@devices.factory()
def electromagnet_sr570_scaler_fy(
    electromagnet_sr570: ElectromagnetSR570,
    electromagnet_scaler_card: ElectromagnetScalerCard1,
) -> CurrentAmpDet:
    return CurrentAmpDet(
        current_amp=electromagnet_sr570.ca2,
        counter=electromagnet_scaler_card.fy,
    )


@devices.factory()
def em_temperature_controller() -> Lakeshore336:
    return Lakeshore336(
        prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-41:",
    )
