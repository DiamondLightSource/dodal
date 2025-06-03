from pathlib import Path

from ophyd_async.core import StrictEnum
from ophyd_async.epics.adpilatus import PilatusDetector

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import HDF5_SUFFIX
from dodal.common.visit import LocalDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.motors import SixAxisGonio
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
set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/tmp"),
        client=LocalDirectoryServiceClient(),
    )
)

PREFIX = BeamlinePrefix(BL)

I23_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(TTL_DETECTOR=1, TTL_SHUTTER=4),
    sources=ZebraSources(),
)


class I23DetectorPositions(StrictEnum):
    IN = "In"
    OUT = "Out"
    SAMPLE_CHANGE = "sample change"


def _is_i23_machine():
    """
    Devices using PVA can only connect from i23 machines, due to the absence of
    PVA gateways at present.
    """
    hostname = get_hostname()
    return hostname.startswith("i23-ws") or hostname.startswith("i23-control")


@device_factory(skip=lambda: not _is_i23_machine())
def oav_pin_tip_detection() -> PinTipDetection:
    """Get the i23 OAV pin-tip detection device."""

    return PinTipDetection(
        f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        "pin_tip_detection",
    )


@device_factory()
def shutter() -> ZebraShutter:
    """Get the i23 zebra controlled shutter."""
    return ZebraShutter(f"{PREFIX.beamline_prefix}-EA-SHTR-01:", "shutter")


@device_factory()
def gonio() -> SixAxisGonio:
    """Get the i23 goniometer"""
    return SixAxisGonio(f"{PREFIX.beamline_prefix}-MO-GONIO-01:")


@device_factory()
def zebra() -> Zebra:
    """Get the i23 zebra"""
    return Zebra(
        name="zebra",
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:ZEBRA:",
        mapping=I23_ZEBRA_MAPPING,
    )


@device_factory()
def pilatus() -> PilatusDetector:
    """Get the i23 pilatus"""
    return PilatusDetector(
        prefix=f"{PREFIX.beamline_prefix}-EA-PILAT-01:",
        path_provider=get_path_provider(),
        drv_suffix="cam1:",
        fileio_suffix=HDF5_SUFFIX,
    )


@device_factory()
def detector_motion() -> Positioner1D[I23DetectorPositions]:
    """Get the i23 detector"""
    return Positioner1D[I23DetectorPositions](
        f"{PREFIX.beamline_prefix}-EA-DET-01:Z",
        datatype=I23DetectorPositions,
    )
