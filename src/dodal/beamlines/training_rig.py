from pathlib import Path

from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.beamlines.device_helpers import DET_SUFFIX, HDF5_SUFFIX
from dodal.common.visit import (
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.devices.training_rig.sample_stage import TrainingRigSampleStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

#
# HTSS Training Rig
#
# A mock-beamline design that is employed at Diamond, consisting of a pair of
# simple motors, a GigE camera and a PandA.
# Since there are multiple rigs whose PVs are identical aside from the prefix,
# this module can be used for any rig. It should fill in the prefix automatically
# if the ${BEAMLINE} environment variable is correctly set, else defaulting
# to p46, which is known to be in good working order.
#

BL = get_beamline_name("p46")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/exports/mybeamline/data/2025"),
        client=LocalDirectoryServiceClient(),
    )
)


@device_factory()
def sample_stage() -> TrainingRigSampleStage:
    return TrainingRigSampleStage(f"{PREFIX.beamline_prefix}-MO-MAP-01:STAGE:")


@device_factory()
def det() -> AravisDetector:
    return AravisDetector(
        f"{PREFIX.beamline_prefix}-EA-DET-01:",
        path_provider=get_path_provider(),
        drv_suffix=DET_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
    )


@device_factory()
def panda() -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-MO-PANDA-01:",
        path_provider=get_path_provider(),
    )
