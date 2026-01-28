from functools import cache
from pathlib import Path

from ophyd_async.core import PathProvider
from ophyd_async.fastcs.eiger import EigerDetector
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    set_beamline as set_utils_beamline,
)
from dodal.common.visit import StaticVisitPathProvider
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorSquad,
)
from dodal.devices.beamlines.i19.access_controlled.blueapi_device import HutchState
from dodal.devices.beamlines.i19.access_controlled.shutter import (
    AccessControlledShutter,
)
from dodal.devices.beamlines.i19.backlight import BacklightPosition
from dodal.devices.beamlines.i19.beamstop import BeamStop
from dodal.devices.beamlines.i19.diffractometer import FourCircleDiffractometer
from dodal.devices.beamlines.i19.pin_col_stages import PinholeCollimatorControl
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix

# NOTE all workstations on I19 default to i19-1 as beamline name
# Unless variable is exported (which is not usually done by scientists)
# NOTE All PVs for both hutches and the optics have the prefix BL19I
BL = "i19-2"
PREFIX = BeamlinePrefix("i19", "I")
set_log_beamline(BL)
set_utils_beamline(BL)

I19_2_COMMISSIONING_INSTR_SESSION: str = "cm40639-5"

I19_2_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(),
    sources=ZebraSources(),
)

devices = DeviceManager()


@devices.fixture
@cache
def path_provider() -> PathProvider:
    return StaticVisitPathProvider(
        BL,
        Path("/dls/i19-2/data/2026/cm44169-1/"),
    )


@devices.factory()
def attenuator_motor_squad() -> AttenuatorMotorSquad:
    return AttenuatorMotorSquad(
        hutch=HutchState.EH2, instrument_session=I19_2_COMMISSIONING_INSTR_SESSION
    )


@devices.factory()
def backlight() -> BacklightPosition:
    return BacklightPosition(prefix=f"{PREFIX.beamline_prefix}-EA-IOC-12:")


@devices.factory()
def beamstop() -> BeamStop:
    return BeamStop(prefix=f"{PREFIX.beamline_prefix}-OP-ABSB-02:")


@devices.factory()
def diffractometer() -> FourCircleDiffractometer:
    return FourCircleDiffractometer(prefix=PREFIX.beamline_prefix)


@devices.factory()
def eiger(path_provider: PathProvider) -> EigerDetector:
    return EigerDetector(
        prefix=PREFIX.beamline_prefix,
        path_provider=path_provider,
        drv_suffix="-EA-EIGER-01:",
        hdf_suffix="-EA-EIGER-01:OD:",
    )


@devices.factory()
def panda(path_provider: PathProvider) -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=path_provider,
    )


@devices.factory()
def pinhole_and_collimator() -> PinholeCollimatorControl:
    return PinholeCollimatorControl(prefix=PREFIX.beamline_prefix)


@devices.factory()
def shutter() -> AccessControlledShutter:
    """Access controlled wrapper for the experiment shutter."""
    return AccessControlledShutter(
        prefix=f"{PREFIX.beamline_prefix}-PS-SHTR-01:",
        hutch=HutchState.EH2,
        instrument_session=I19_2_COMMISSIONING_INSTR_SESSION,
    )


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def zebra() -> Zebra:
    return Zebra(
        mapping=I19_2_ZEBRA_MAPPING,
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-03:",
    )
