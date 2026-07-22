from ophyd_async.core import DeviceVector
from ophyd_async.epics.core import epics_signal_r

from dodal.beamlines.i06_shared import devices as i06_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i06_1 import DiffractionDichroism
from dodal.devices.beamlines.i06_1.magnets import (
    MagnetThreeAxesRampRateController,
    SuperConductingMagnetController,
)
from dodal.devices.motors import XYThetaStage
from dodal.devices.scaler_card import ScalerCardChannels, ScalerCardController
from dodal.devices.temperture_controller import Lakeshore336
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
def mag_ramp_rate() -> MagnetThreeAxesRampRateController:
    return MagnetThreeAxesRampRateController(f"{J_PREFIX.beamline_prefix}-EA-SMC")


@devices.factory()
def scmc(
    mag_ramp_rate: MagnetThreeAxesRampRateController,
) -> SuperConductingMagnetController:
    return SuperConductingMagnetController(
        f"{J_PREFIX.beamline_prefix}-EA-MAG-01:", mag_ramp_rate
    )


@devices.factory()
def scaler2() -> ScalerCardController:
    return ScalerCardController(
        f"{I_PREFIX.beamline_prefix}-DI-8512-02:",
        start_count_suffix="STARTCOUNT",
        count_suffix="PRESET",
    )


@devices.factory()
def mag_dets(scaler2: ScalerCardController):
    """Used to measure during a fly scan of a MagnetAxis for the
    SuperConductingMagnetController device.
    """
    prefix = f"{J_PREFIX.beamline_prefix}-EA-MAG-01:"
    return ScalerCardChannels(
        channels=DeviceVector(
            {
                # Change to DeviceMap when on ophyd-async 0.20
                0: epics_signal_r(float, prefix + "TEYC-RAW"),  # TEY
                1: epics_signal_r(float, prefix + "FDUC-RAW"),  # FDU
                2: epics_signal_r(float, prefix + "FDDC-RAW"),  # FDD
                3: epics_signal_r(float, prefix + "90DC-RAW"),  # D90
                4: epics_signal_r(float, prefix + "FIELDC-RAW"),  # FFZ
            }
        ),
        controller=scaler2,
    )
