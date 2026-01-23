from daq_config_server.client import ConfigServer

from dodal.device_manager import DeviceManager
from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorWithDSpacing,
    PitchAndRollCrystal,
    StationaryCrystal,
)
from dodal.devices.i09_1_shared.hard_energy import HardEnergy, HardInsertionDeviceEnergy
from dodal.devices.i09_1_shared.hard_undulator_functions import (
    I09HardLutProvider,
    calculate_energy_i09_hu,
    calculate_gap_i09_hu,
)
from dodal.devices.undulator import UndulatorInMm, UndulatorOrder
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i09-1-shared")
I_PREFIX = BeamlinePrefix(BL, suffix="I")

devices = DeviceManager()

I09_1_CONF_CLIENT = ConfigServer()
LOOK_UPTABLE_FILE = "/dls_sw/i09-1/software/gda/workspace_git/gda-diamond.git/configurations/i09-1-shared/lookupTables/IIDCalibrationTable.txt"


@devices.factory()
def dcm() -> DoubleCrystalMonochromatorWithDSpacing[
    PitchAndRollCrystal, StationaryCrystal
]:
    return DoubleCrystalMonochromatorWithDSpacing[
        PitchAndRollCrystal, StationaryCrystal
    ](f"{I_PREFIX.beamline_prefix}-MO-DCM-01:", PitchAndRollCrystal, StationaryCrystal)


@devices.factory()
def undulator() -> UndulatorInMm:
    return UndulatorInMm(prefix=f"{I_PREFIX.insertion_prefix}-MO-SERVC-01:")


@devices.factory()
def harmonics() -> UndulatorOrder:
    return UndulatorOrder()


@devices.factory()
def hu_id_energy(
    harmonics: UndulatorOrder, undulator: UndulatorInMm
) -> HardInsertionDeviceEnergy:
    return HardInsertionDeviceEnergy(
        undulator_order=harmonics,
        undulator=undulator,
        lut_provider=I09HardLutProvider(I09_1_CONF_CLIENT, LOOK_UPTABLE_FILE),
        gap_to_energy_func=calculate_energy_i09_hu,
        energy_to_gap_func=calculate_gap_i09_hu,
    )


@devices.factory()
def hu_energy(
    dcm: DoubleCrystalMonochromatorWithDSpacing, hu_id_energy: HardInsertionDeviceEnergy
) -> HardEnergy:
    return HardEnergy(
        dcm=dcm,
        undulator_energy=hu_id_energy,
    )
