from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.motors import SixAxisGonio
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name, get_hostname

BL = get_beamline_name("i23")
set_log_beamline(BL)
set_utils_beamline(BL)

PREFIX = BeamlinePrefix(BL)

I23_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(TTL_DETECTOR=1, TTL_SHUTTER=4),
    sources=ZebraSources(),
    AND_GATE_FOR_AUTO_SHUTTER=2,
)


def _is_i23_machine():
    """
    Devices using PVA can only connect from i23 machines, due to the absence of
    PVA gateways at present.
    """
    hostname = get_hostname()
    return hostname.startswith("i23-ws") or hostname.startswith("i23-control")


@device_factory(skip=lambda: not _is_i23_machine())
def oav_pin_tip_detection() -> PinTipDetection:
    """Get the i23 OAV pin-tip detection device"""

    return PinTipDetection(
        f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        "pin_tip_detection",
    )


@device_factory()
def gonio() -> SixAxisGonio:
    """Get the i23 goniometer"""

    return SixAxisGonio(
        f"{PREFIX.beamline_prefix}-MO-GONIO-01:",
    )


@device_factory()
def zebra() -> Zebra:
    """Get the i23 zebra"""
    return Zebra(
        name="zebra",
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:ZEBRA:",
        mapping=I23_ZEBRA_MAPPING,
    )


@device_factory()
def zebra() -> Zebra:
    """Get the i23 zebra"""
    return Zebra(
        name="zebra",
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:ZEBRA:",
        mapping=I23_ZEBRA_MAPPING,
    )
