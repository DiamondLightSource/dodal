from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.crystal_metadata import (
    MaterialsEnum,
    make_crystal_metadata_from_material,
)
from dodal.devices.i16.dcm import DCM
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i16")
PREFIX = BeamlinePrefix(BL, suffix="I")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()

# dodal connect should work again after this https://jira.diamond.ac.uk/browse/I16-960
@device_factory()
def dcm() -> DCM:
    return DCM(
        prefix=f"{PREFIX.beamline_prefix}-OP-DCM-01:",
        temperature_prefix=f"{PREFIX.beamline_prefix}-OP-DCM-01:",
        crystal_1_metadata=make_crystal_metadata_from_material(
            MaterialsEnum.Si, (1, 1, 1)
        ),
        crystal_2_metadata=make_crystal_metadata_from_material(
            MaterialsEnum.Si, (1, 1, 1)
        ),
    )
