from pathlib import Path

from ophyd_async.core import StaticDirectoryProvider
from ophyd_async.epics.areadetector.aravis import AravisDetector

from dodal.common.beamlines.beamline_utils import device_instantiation
from dodal.devices.htss.sample_stage import TrainingRigSampleStage


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
