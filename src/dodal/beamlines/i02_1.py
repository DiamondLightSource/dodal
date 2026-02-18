"""Beamline i02-1 is also known as VMXm, or I02J."""

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.attenuator.attenuator import EnumFilterAttenuator
from dodal.devices.attenuator.filter_selections import (
    I02_1FilterFourSelections,
    I02_1FilterOneSelections,
    I02_1FilterThreeSelections,
    I02_1FilterTwoSelections,
)
from dodal.devices.beamlines.i02_1.fast_grid_scan import ZebraFastGridScanTwoD
from dodal.devices.beamlines.i02_1.flux import Flux
from dodal.devices.beamlines.i02_1.sample_motors import SampleMotors
from dodal.devices.common_dcm import DoubleCrystalMonochromatorBase, StationaryCrystal
from dodal.devices.eiger import EigerDetector
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.undulator import UndulatorInKeV
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i02-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)
DAQ_CONFIGURATION_PATH = "/dls_sw/i02-1/software/daq_configuration"

I02_1_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(TTL_EIGER=4),
    sources=ZebraSources(),
)

devices = DeviceManager()


@devices.v1_init(
    EigerDetector, prefix=f"{PREFIX.beamline_prefix}-EA-EIGER-01:", wait=False
)
def eiger(eiger: EigerDetector) -> EigerDetector:
    return eiger


@devices.factory()
def undulator(daq_configuration_path: str) -> UndulatorInKeV:
    return UndulatorInKeV(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        id_gap_lookup_table_path=f"{daq_configuration_path}/lookup/BeamLine_Undulator_toGap.txt",
    )


@devices.factory()
def zebra_fast_grid_scan() -> ZebraFastGridScanTwoD:
    return ZebraFastGridScanTwoD(
        prefix=f"{PREFIX.beamline_prefix}-MO-SAMP-11:",
        motion_controller_prefix="BL02J-MO-STEP-11:",
    )


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def zebra() -> Zebra:
    return Zebra(
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:",
        mapping=I02_1_ZEBRA_MAPPING,
    )


@devices.factory()
def dcm() -> DoubleCrystalMonochromatorBase:
    return DoubleCrystalMonochromatorBase(
        f"{PREFIX.beamline_prefix}-MO-DCM-01:",
        xtal_1=StationaryCrystal,
        xtal_2=StationaryCrystal,
    )


@devices.fixture
def daq_configuration_path() -> str:
    return DAQ_CONFIGURATION_PATH


@devices.factory()
def s4_slit_gaps() -> Slits:
    return Slits(f"{PREFIX.beamline_prefix}-AL-SLITS-04:")


@devices.factory(use_factory_name=False)
def goniometer() -> SampleMotors:
    return SampleMotors(f"{PREFIX.beamline_prefix}-MO-SAMP-01:", name="gonio")


@devices.factory()
def flux() -> Flux:
    return Flux(f"{PREFIX.beamline_prefix}-EA-FLUX-01:")


@devices.factory()
def attenuator() -> EnumFilterAttenuator:
    return EnumFilterAttenuator(
        f"{PREFIX.beamline_prefix}-OP-ATTN-01:",
        (
            I02_1FilterOneSelections,
            I02_1FilterTwoSelections,
            I02_1FilterThreeSelections,
            I02_1FilterFourSelections,
        ),
    )
