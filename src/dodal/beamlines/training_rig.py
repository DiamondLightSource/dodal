from pathlib import Path

from ophyd_async.core import StaticDirectoryProvider
from ophyd_async.epics.areadetector.aravis import AravisDetector

from dodal.common.beamlines.beamline_utils import device_instantiation
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.training_rig.sample_stage import TrainingRigSampleStage
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

#
# HTSS Training Rig
#
# A mock-beamline design that is employed at Diamond, consisting of a pair of
# simple motors, a GigE camera and a PandA.
# Since there are multiple rigs whose PVs are identical aside from the prefix,
# this module can be used for any rig. It should fill in the prefix automatically
# if the ${BEAMLINE} environment variable is correctly set. It currently defaults
# to p47.
#

BL = get_beamline_name("p47")
set_log_beamline(BL)
set_utils_beamline(BL)


def sample_stage(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> TrainingRigSampleStage:
    return device_instantiation(
        TrainingRigSampleStage,
        "sample_stage",
        "-MO-MAP-01:STAGE:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def det(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> AravisDetector:
    directory_provider = StaticDirectoryProvider(Path("/exports/mybeamline/data"))
    return device_instantiation(
        AravisDetector,
        "det",
        "-EA-DET-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        drv_suffix="DET:",
        hdf_suffix="HDF5:",
        directory_provider=directory_provider,
    )
