from ophyd_async.core import DeviceMap
from ophyd_async.epics.core import epics_signal_r

from dodal.beamlines.i06_shared import devices as i06_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i06_1 import DiffractionDichroism
from dodal.devices.beamlines.i06_1.magnet import (
    SuperConductingMagnetController,
    ThreeMagnetAxisPowerSupply,
)
from dodal.devices.beamlines.i06_1.magnet.temperature_controller import (
    SuperConductingMagnetTemperatureController,
)
from dodal.devices.motors import XYThetaStage
from dodal.devices.scaler_card import ScalerCardChannels, ScalerCardController
from dodal.devices.temperature_controller import Lakeshore336
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i06_1")
I_PREFIX = BeamlinePrefix(BL, suffix="I")
J_PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(i06_shared_devices)


@devices.factory()
def ls336_cooling() -> Lakeshore336:
    return Lakeshore336(prefix=f"{J_PREFIX.beamline_prefix}-EA-TCTRL-02:")


@devices.factory()
def ls336_heating() -> Lakeshore336:
    return Lakeshore336(prefix=f"{J_PREFIX.beamline_prefix}-EA-TCTRL-03:")


@devices.factory()
def xabs() -> XYThetaStage:
    return XYThetaStage(f"{J_PREFIX.beamline_prefix}-EA-XABS-01:")


@devices.factory()
def dd() -> DiffractionDichroism:
    return DiffractionDichroism(f"{J_PREFIX.beamline_prefix}-EA-DDIFF-01:")


@devices.factory()
def scm_temp_controller() -> SuperConductingMagnetTemperatureController:
    return SuperConductingMagnetTemperatureController(
        prefix=f"{J_PREFIX.beamline_prefix}-EA-TCTRL-01:"
    )


@devices.factory()
def scm_psu() -> ThreeMagnetAxisPowerSupply:
    return ThreeMagnetAxisPowerSupply(f"{J_PREFIX.beamline_prefix}-EA-SMC")


@devices.factory()
def scmc(
    scm_psu: ThreeMagnetAxisPowerSupply,
) -> SuperConductingMagnetController:
    return SuperConductingMagnetController(
        f"{J_PREFIX.beamline_prefix}-EA-MAG-01:", scm_psu
    )


@devices.factory()
def scaler2_controller() -> ScalerCardController:
    return ScalerCardController(
        f"{I_PREFIX.beamline_prefix}-DI-8512-02:",
        start_count_suffix="STARTCOUNT",
        count_suffix="PRESET",
    )


@devices.factory()
def scaler2_mag(scaler2_controller: ScalerCardController):
    """Magnet scaler card channels for scaler2_controller."""
    mag_prefix = f"{J_PREFIX.beamline_prefix}-EA-MAG-01:"
    current_amp_pv = f"{I_PREFIX.beamline_prefix}-DI-IAMP-04:I1C-RAW"
    return ScalerCardChannels(
        channels=DeviceMap(
            {
                "tey": epics_signal_r(float, mag_prefix + "TEYC-RAW"),
                "i0": epics_signal_r(float, current_amp_pv),
                "fdu": epics_signal_r(float, mag_prefix + "FDUC-RAW"),
                "fdd": epics_signal_r(float, mag_prefix + "FDDC-RAW"),
                "d90": epics_signal_r(float, mag_prefix + "90DC-RAW"),
                "ffz": epics_signal_r(float, mag_prefix + "FIELDC-RAW"),
            }
        ),
        controller=scaler2_controller,
    )


@devices.factory()
def scaler2_ppj(scaler2_controller: ScalerCardController):
    """Patch Panel J channels for scaler2_controller."""
    prefix = f"{J_PREFIX.beamline_prefix}-EA-USER-01:"
    return ScalerCardChannels(
        channels=DeviceMap(
            {
                "ca61sr": epics_signal_r(float, prefix + "SC1-RAW"),
                "ca62sr": epics_signal_r(float, prefix + "SC2-RAW"),
                "ca63sr": epics_signal_r(float, prefix + "SC3-RAW"),
                "ca64sr": epics_signal_r(float, prefix + "SC4-RAW"),
                "ca65sr": epics_signal_r(float, prefix + "SC5-RAW"),
                "ca66sr": epics_signal_r(float, prefix + "SC6-RAW"),
                "ca67sr": epics_signal_r(float, prefix + "SC7-RAW"),
                "ca68sr": epics_signal_r(float, prefix + "SC8-RAW"),
            }
        ),
        controller=scaler2_controller,
    )
