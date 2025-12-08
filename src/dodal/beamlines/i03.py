from functools import cache

from ophyd_async.core import PathProvider, Reference
from ophyd_async.fastcs.eiger import EigerDetector as FastEiger
from ophyd_async.fastcs.panda import HDFPanda
from yarl import URL

from dodal.common.beamlines.beamline_parameters import get_beamline_parameters
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.udc_directory_provider import PandASubpathProvider
from dodal.device_manager import DeviceManager
from dodal.devices.aperturescatterguard import (
    AperturePosition,
    ApertureScatterguard,
    load_positions_from_beamline_parameters,
)
from dodal.devices.attenuator.attenuator import BinaryFilterAttenuator
from dodal.devices.backlight import Backlight
from dodal.devices.baton import Baton
from dodal.devices.collimation_table import CollimationTable
from dodal.devices.cryostream import (
    CryoStreamGantry,
    OxfordCryoJet,
    OxfordCryoStream,
)
from dodal.devices.detector.detector_motion import DetectorMotion
from dodal.devices.diamond_filter import DiamondFilter, I03Filters
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import PandAFastGridScan, ZebraFastGridScanThreeD
from dodal.devices.fluorescence_detector_motion import FluorescenceDetector
from dodal.devices.flux import Flux
from dodal.devices.focusing_mirror import FocusingMirrorWithStripes, MirrorVoltages
from dodal.devices.hutch_shutter import HutchShutter
from dodal.devices.i03 import Beamstop
from dodal.devices.i03.beamsize import Beamsize
from dodal.devices.i03.dcm import DCM
from dodal.devices.i03.undulator_dcm import UndulatorDCM
from dodal.devices.ipin import IPin
from dodal.devices.motors import XYZStage
from dodal.devices.oav.oav_detector import OAVBeamCentreFile
from dodal.devices.oav.oav_parameters import OAVConfigBeamCentre
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.qbpm import QBPM
from dodal.devices.robot import BartRobot
from dodal.devices.s4_slit_gaps import S4SlitGaps
from dodal.devices.scintillator import Scintillator
from dodal.devices.smargon import Smargon
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.thawer import Thawer
from dodal.devices.undulator import UndulatorInKeV
from dodal.devices.webcam import Webcam
from dodal.devices.xbpm_feedback import XBPMFeedback
from dodal.devices.xspress3.xspress3 import Xspress3
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    ZebraMapping,
    ZebraSources,
    ZebraTTLOutputs,
)
from dodal.devices.zebra.zebra_controlled_shutter import ZebraShutter
from dodal.devices.zocalo import ZocaloResults, ZocaloSource
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

ZOOM_PARAMS_FILE = (
    "/dls_sw/i03/software/gda/configurations/i03-config/xml/jCameraManZoomLevels.xml"
)
DISPLAY_CONFIG = "/dls_sw/i03/software/gda_versions/var/display.configuration"
DAQ_CONFIGURATION_PATH = "/dls_sw/i03/software/daq_configuration"

BL = get_beamline_name("i03")
set_log_beamline(BL)
set_utils_beamline(BL)

I03_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraTTLOutputs(TTL_DETECTOR=1, TTL_SHUTTER=2, TTL_XSPRESS3=3, TTL_PANDA=4),
    sources=ZebraSources(),
)

PREFIX = BeamlinePrefix(BL)

devices = DeviceManager()


@devices.fixture
@cache
def path_provider() -> PathProvider:
    return PandASubpathProvider()


@devices.fixture
def daq_configuration_path() -> str:
    return DAQ_CONFIGURATION_PATH


@devices.factory()
def aperture_scatterguard() -> ApertureScatterguard:
    params = get_beamline_parameters()
    return ApertureScatterguard(
        aperture_prefix=f"{PREFIX.beamline_prefix}-MO-MAPT-01:",
        scatterguard_prefix=f"{PREFIX.beamline_prefix}-MO-SCAT-01:",
        loaded_positions=load_positions_from_beamline_parameters(params),
        tolerances=AperturePosition.tolerances_from_gda_params(params),
    )


@devices.factory()
def attenuator() -> BinaryFilterAttenuator:
    return BinaryFilterAttenuator(
        prefix=f"{PREFIX.beamline_prefix}-EA-ATTN-01:",
        num_filters=16,
    )


@devices.factory()
def beamstop() -> Beamstop:
    return Beamstop(
        prefix=f"{PREFIX.beamline_prefix}-MO-BS-01:",
        beamline_parameters=get_beamline_parameters(),
    )


@devices.factory()
def dcm() -> DCM:
    return DCM(prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:")


@devices.factory()
def vfm() -> FocusingMirrorWithStripes:
    return FocusingMirrorWithStripes(
        prefix=f"{PREFIX.beamline_prefix}-OP-VFM-01:",
        bragg_to_lat_lut_path=DAQ_CONFIGURATION_PATH
        + "/lookup/BeamLineEnergy_DCM_VFM_x_converter.txt",
        x_suffix="LAT",
        y_suffix="VERT",
    )


@devices.factory()
def mirror_voltages() -> MirrorVoltages:
    return MirrorVoltages(
        prefix=f"{PREFIX.beamline_prefix}-MO-PSU-01:",
        daq_configuration_path=DAQ_CONFIGURATION_PATH,
    )


@devices.factory()
def backlight() -> Backlight:
    return Backlight(prefix=PREFIX.beamline_prefix)


@devices.factory()
def detector_motion() -> DetectorMotion:
    return DetectorMotion(
        device_prefix=f"{PREFIX.beamline_prefix}-MO-DET-01:",
        pmac_prefix=f"{PREFIX.beamline_prefix}-MO-PMAC-02:",
    )


@devices.v1_init(EigerDetector, prefix="BL03I-EA-EIGER-01:", wait=False)
def eiger(eiger: EigerDetector) -> EigerDetector:
    return eiger


@devices.factory()
def fastcs_eiger(path_provider: PathProvider) -> FastEiger:
    return FastEiger(
        prefix=PREFIX.beamline_prefix,
        path_provider=path_provider,
        drv_suffix="-EA-EIGER-02:",
        hdf_suffix="-EA-EIGER-01:OD:",
    )


@devices.factory()
def zebra_fast_grid_scan() -> ZebraFastGridScanThreeD:
    return ZebraFastGridScanThreeD(
        prefix=f"{PREFIX.beamline_prefix}-MO-SGON-01:",
    )


@devices.factory()
def panda_fast_grid_scan() -> PandAFastGridScan:
    """This is used instead of the zebra_fast_grid_scan device when using the PandA."""
    return PandAFastGridScan(prefix=f"{PREFIX.beamline_prefix}-MO-SGON-01:")


@devices.factory()
def oav(
    params: OAVConfigBeamCentre | None = None,
) -> OAVBeamCentreFile:
    return OAVBeamCentreFile(
        prefix=f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        config=params or OAVConfigBeamCentre(ZOOM_PARAMS_FILE, DISPLAY_CONFIG),
    )


@devices.factory()
def pin_tip_detection() -> PinTipDetection:
    return PinTipDetection(f"{PREFIX.beamline_prefix}-DI-OAV-01:")


@devices.factory()
def smargon() -> Smargon:
    return Smargon(f"{PREFIX.beamline_prefix}-MO-SGON-01:")


@devices.factory()
def s4_slit_gaps() -> S4SlitGaps:
    return S4SlitGaps(f"{PREFIX.beamline_prefix}-AL-SLITS-04:")


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def undulator(baton: Baton, daq_configuration_path: str) -> UndulatorInKeV:
    return UndulatorInKeV(
        f"{BeamlinePrefix(BL).insertion_prefix}-MO-SERVC-01:",
        id_gap_lookup_table_path=f"{daq_configuration_path}/lookup/BeamLine_Undulator_toGap.txt",
        baton=baton,
    )


@devices.factory()
def undulator_dcm(
    undulator: UndulatorInKeV, dcm: DCM, daq_configuration_path: str
) -> UndulatorDCM:
    return UndulatorDCM(
        undulator=undulator,
        dcm=dcm,
        daq_configuration_path=daq_configuration_path,
    )


@devices.factory()
def zebra() -> Zebra:
    return Zebra(
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:",
        mapping=I03_ZEBRA_MAPPING,
    )


@devices.factory()
def xspress3mini() -> Xspress3:
    return Xspress3(f"{PREFIX.beamline_prefix}-EA-XSP3-01:")


@devices.factory()
def panda(path_provider: PathProvider) -> HDFPanda:
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=path_provider,
    )


@devices.factory()
def sample_shutter() -> ZebraShutter:
    return ZebraShutter(f"{PREFIX.beamline_prefix}-EA-SHTR-01:")


@devices.factory()
def hutch_shutter() -> HutchShutter:
    return HutchShutter(f"{PREFIX.beamline_prefix}-PS-SHTR-01:")


@devices.factory()
def flux() -> Flux:
    return Flux(f"{PREFIX.beamline_prefix}-MO-FLUX-01:")


@devices.factory()
def xbpm_feedback(baton: Baton) -> XBPMFeedback:
    return XBPMFeedback(f"{PREFIX.beamline_prefix}-EA-FDBK-01:", baton=baton)


@devices.factory()
def zocalo() -> ZocaloResults:
    return ZocaloResults(results_source=ZocaloSource.GPU)


@devices.factory()
def robot() -> BartRobot:
    return BartRobot(f"{PREFIX.beamline_prefix}-MO-ROBOT-01:")


@devices.factory()
def webcam() -> Webcam:
    return Webcam(url=URL("http://i03-webcam1/axis-cgi/jpg/image.cgi"))


@devices.factory()
def thawer() -> Thawer:
    return Thawer(f"{PREFIX.beamline_prefix}-EA-THAW-01")


@devices.factory()
def lower_gonio() -> XYZStage:
    return XYZStage(f"{PREFIX.beamline_prefix}-MO-GONP-01:")


@devices.factory()
def cryostream() -> OxfordCryoStream:
    return OxfordCryoStream(f"{PREFIX.beamline_prefix}-EA-CSTRM-01:")


@devices.factory()
def cryojet() -> OxfordCryoJet:
    return OxfordCryoJet(f"{PREFIX.beamline_prefix}-EA-CJET-01:")


@devices.factory()
def cryostream_gantry() -> CryoStreamGantry:
    return CryoStreamGantry(PREFIX.beamline_prefix)


@devices.factory()
def diamond_filter() -> DiamondFilter[I03Filters]:
    return DiamondFilter[I03Filters](
        f"{PREFIX.beamline_prefix}-MO-FLTR-01:Y", I03Filters
    )


@devices.factory()
def qbpm() -> QBPM:
    return QBPM(f"{PREFIX.beamline_prefix}-DI-QBPM-01:")


@devices.factory()
def baton() -> Baton:
    return Baton(f"{PREFIX.beamline_prefix}-CS-BATON-01:")


@devices.factory()
def fluorescence_det_motion() -> FluorescenceDetector:
    return FluorescenceDetector(f"{PREFIX.beamline_prefix}-EA-FLU-01:")


@devices.factory()
def scintillator(aperture_scatterguard: ApertureScatterguard) -> Scintillator:
    return Scintillator(
        f"{PREFIX.beamline_prefix}-MO-SCIN-01:",
        Reference(aperture_scatterguard),
        get_beamline_parameters(),
    )


@devices.factory()
def collimation_table() -> CollimationTable:
    return CollimationTable(prefix=f"{PREFIX.beamline_prefix}-MO-TABLE-01")


@devices.factory()
def beamsize(aperture_scatterguard: ApertureScatterguard) -> Beamsize:
    return Beamsize(aperture_scatterguard)


@devices.factory()
def ipin() -> IPin:
    return IPin(f"{PREFIX.beamline_prefix}-EA-PIN-01:")
