from functools import cache
from pathlib import Path

from daq_config_server import ConfigClient
from ophyd_async.core import InOut, PathProvider, StrictEnum
from ophyd_async.epics.adpilatus import PilatusDetector

from dodal.beamlines.aithre import DISPLAY_CONFIG, ZOOM_PARAMS_FILE
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import HDF5_SUFFIX
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.device_manager import DeviceManager
from dodal.devices.motors import SixAxisGonio
from dodal.devices.oav.oav_detector import OAVBeamCentreFile
from dodal.devices.oav.oav_parameters import OAVConfigBeamCentre
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.positioner import Positioner1D
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.devices.zebra.zebra_controlled_shutter import ZebraShutter
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name, get_hostname

BL = get_beamline_name("i23")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()

@devices.fixture
@cache
def config_client() -> ConfigClient:
    return ConfigClient()

@devices.fixture
@cache
def path_provider() -> PathProvider:
    return StaticVisitPathProvider(
        BL,
        Path("/tmp"),
        client=LocalDirectoryServiceClient(),
    )


I23_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(TTL_DETECTOR=1, TTL_SHUTTER=4),
    sources=ZebraSources(),
)


class I23DetectorPositions(StrictEnum):
    IN = InOut.IN.value
    OUT = InOut.OUT.value
    SAMPLE_CHANGE = "sample change"


def _is_i23_machine():
    """Devices using PVA can only connect from i23 machines, due to the absence of
    PVA gateways at present.
    """
    hostname = get_hostname()
    return hostname.startswith("i23-ws") or hostname.startswith("i23-control")

@devices.factory()
def oav(config_client) -> OAVBeamCentreFile:
    return OAVBeamCentreFile(
        prefix=f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        config=OAVConfigBeamCentre(ZOOM_PARAMS_FILE, DISPLAY_CONFIG, config_client),
    )

@devices.factory()
def pin_tip_detection() -> PinTipDetection:
    return PinTipDetection(f"{PREFIX.beamline_prefix}-DI-OAV-01:")

@devices.factory()
def shutter() -> ZebraShutter:
    return ZebraShutter(f"{PREFIX.beamline_prefix}-EA-SHTR-01:")


@devices.factory()
def gonio() -> SixAxisGonio:
    return SixAxisGonio(f"{PREFIX.beamline_prefix}-MO-GONIO-01:")


@devices.factory()
def zebra() -> Zebra:
    return Zebra(
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:ZEBRA:",
        mapping=I23_ZEBRA_MAPPING,
    )


@devices.factory()
def pilatus(path_provider: PathProvider) -> PilatusDetector:
    return PilatusDetector(
        prefix=f"{PREFIX.beamline_prefix}-EA-PILAT-01:",
        path_provider=path_provider,
        drv_suffix="cam1:",
        fileio_suffix=HDF5_SUFFIX,
    )


@devices.factory()
def detector_motion() -> Positioner1D[I23DetectorPositions]:
    return Positioner1D[I23DetectorPositions](
        f"{PREFIX.beamline_prefix}-EA-DET-01:Z",
        datatype=I23DetectorPositions,
    )
