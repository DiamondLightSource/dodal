from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.p60 import R4000, LabXraySource, LabXraySourceReadable
from dodal.devices.electron_analyser.base import DualEnergySource
from dodal.devices.selectable_source import SourceSelector
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

"""
NOTE: Due to p60 not having a CA gateway, PVs are not available remotely and you need to
be on the beamline network to access them so a remote `dodal connect p60` will fail.
"""

BL = get_beamline_name("p60")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.factory()
def source_selector() -> SourceSelector:
    return SourceSelector()


@devices.factory()
def al_kalpha_source() -> LabXraySourceReadable:
    return LabXraySourceReadable(LabXraySource.AL_KALPHA)


@devices.factory()
def mg_kalpha_source() -> LabXraySourceReadable:
    return LabXraySourceReadable(LabXraySource.MG_KALPHA)


@devices.factory()
def dual_energy_source(
    al_kalpha_source: LabXraySourceReadable,
    mg_kalpha_source: LabXraySourceReadable,
    source_selector: SourceSelector,
) -> DualEnergySource:
    return DualEnergySource(
        al_kalpha_source.energy_ev,
        mg_kalpha_source.energy_ev,
        source_selector.selected_source,
    )


# Connect will work again after this work completed
# https://jira.diamond.ac.uk/browse/P60-13
@devices.factory()
def r4000(dual_energy_source: DualEnergySource) -> R4000:
    return R4000(f"{PREFIX.beamline_prefix}-EA-DET-01:CAM:", dual_energy_source)
