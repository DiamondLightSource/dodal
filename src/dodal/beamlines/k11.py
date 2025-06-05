from pathlib import Path

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import RemoteDirectoryServiceClient, StaticVisitPathProvider
from dodal.devices.motors import MotorGroup
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

beamline = get_beamline_name("k11")
PREFIX = BeamlinePrefix(beamline)
set_log_beamline(beamline)
set_utils_beamline(beamline)

set_path_provider(
    StaticVisitPathProvider(
        beamline,
        Path("/dls/k11/data/2025/cm40627-3"),
        client=RemoteDirectoryServiceClient("https://k11-control:8088/api"),
    )
)


@device_factory()
def kb() -> MotorGroup:
    """KB mirrors in pixel space"""
    return MotorGroup(
        name="kb",
        motor_name_to_pv={
            "x": f"{PREFIX.beamline_prefix}-OP-KBM-01:CS:X",
            "y": f"{PREFIX.beamline_prefix}-OP-KBM-01:CS:Y",
        },
    )
