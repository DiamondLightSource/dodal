from dodal.beamlines.b07_shared import devices as b07_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.b07_1 import (
    ChannelCutMonochromator,
    Grating,
    SpecsPhoibos,
)
from dodal.devices.electron_analyser.base import EnergySource
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("b07-1")
C_PREFIX = BeamlinePrefix(BL, suffix="C")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(b07_shared_devices)


@devices.factory()
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{C_PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=Grating,
    )


@devices.factory()
def ccmc() -> ChannelCutMonochromator:
    return ChannelCutMonochromator(prefix=f"{C_PREFIX.beamline_prefix}-OP-CCM-01:")


@devices.factory()
def energy_source(pgm: PlaneGratingMonochromator) -> EnergySource:
    return EnergySource(pgm.energy.user_readback)


# CAM:IMAGE will fail to connect outside the beamline network,
# see https://github.com/DiamondLightSource/dodal/issues/1852
@devices.factory()
def analyser(energy_source: EnergySource) -> SpecsPhoibos:
    return SpecsPhoibos(
        prefix=f"{C_PREFIX.beamline_prefix}-EA-DET-01:CAM:",
        energy_source=energy_source,
    )
