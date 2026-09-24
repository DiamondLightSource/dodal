from daq_config_server.client import ConfigClient
from yarl import URL

from dodal.common.beamlines.commissioning_mode import set_commissioning_signal
from dodal.device_manager import DeviceManager
from dodal.devices.aperturescatterguard import ApertureScatterguard, load_positions_from_beamline_parameters, \
    AperturePosition
from dodal.devices.attenuator.attenuator import BinaryFilterAttenuator
from dodal.devices.backlight import Backlight
from dodal.devices.baton import Baton
from dodal.devices.beamlines.i03.beamsize import Beamsize
from dodal.devices.beamlines.i03.dcm import DCM
from dodal.devices.beamlines.i03.undulator_dcm import UndulatorDCM
from dodal.devices.collimation_table import CollimationTable
from dodal.devices.cryostream import OxfordCryoStream, OxfordCryoJet, CryoStreamGantry
from dodal.devices.detector.detector_motion import DetectorMotion
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import ZebraFastGridScanThreeD, PandAFastGridScan
from dodal.devices.flux import Flux
from dodal.devices.focusing_mirror import FocusingMirrorWithStripes, MirrorVoltages
from dodal.devices.motors import XYZWrappedOmegaStage, XYZStage
from dodal.devices.mx_phase1.beamstop import Beamstop
from dodal.devices.oav.oav_detector import OAVBeamCentreFile
from dodal.devices.oav.oav_parameters import OAVConfigBeamCentre
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.robot import BartRobot
from dodal.devices.slits import MinimalSlits
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.thawer import Thawer
from dodal.devices.undulator import UndulatorInKeV
from dodal.devices.webcam import Webcam
from dodal.devices.xbpm_feedback import XBPMFeedback
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import ZebraMapping, ZebraOutputs, ZebraSources
from dodal.devices.zebra.zebra_controlled_shutter import MXZebraShutter
from dodal.devices.zocalo import ZocaloResults, ZocaloSource
from dodal.log import set_beamline as set_log_beamline
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.utils import get_beamline_name, BeamlinePrefix
from ophyd_async.core import PathProvider
from ophyd_async.fastcs.panda import HDFPanda

BL = get_beamline_name("i04-1")

set_log_beamline(BL)
set_utils_beamline(BL)

PREFIX = BeamlinePrefix(BL)

devices = DeviceManager()

BEAMLINE_PARAMETERS_PATH = (
    "/dls_sw/i04-1/software/daq_configuration/domain/beamlineParameters"
)

ZOOM_PARAMS_FILE = (
    "/dls_sw/i04-1/software/gda/config/xml/jCameraManZoomLevels.xml"
)

DISPLAY_CONFIG = "/dls_sw/i04-1/software/gda_versions/var/display.configuration"
DAQ_CONFIGURATION_PATH = "/dls_sw/i04-1/software/daq_configuration"

# TODO verify this
I04_ZEBRA_MAPPING = ZebraMapping(
    outputs=ZebraOutputs(TTL_DETECTOR=1, TTL_SHUTTER=2, TTL_XSPRESS3=3, TTL_PANDA=4),
    sources=ZebraSources(),
)


@devices.fixture
def daq_configuration_path() -> str:
    return DAQ_CONFIGURATION_PATH

# Tasks:
# Deploy DAQ Config Server
# Implement / select implementation of Beamsize
# Simplify detector motion to remove unneeded PVs
# Check Eiger ID Number
# Check Zebra is configured same as I03 for gridscan, rotation
# Update Zebra FGS parameters in smargon as different from I03
# Validate correct configuration file names
# Refactor gonio support for LoadCentreCollect since no Phi on i04-1
# Rename s4 slits to something more suitably generic
# Refactor/replace robot load / change energy plan to allow fixed energy
# Clarify shared optics with I04
# Remove panda from composite
# Make sample shutter control more generic if needed
# Remove VFM, MirrorVoltages, DCM, UndulatorDCM from needed composite items
# Different beamstop implementation
# Customise agamemnon.py, supervisor for i04-1
# GDA baton for i04-1
# Customise UDC default state:
#   * Use cryostream, remove cryojet, gantry
#   * Fluorescence detector in/out
#   * Hutch shutter check


# Questions for Chris:
# What is i04-1 doing instead of aperture-scatterguard for beam size
# XBPM feedback - do we use it?
# No XBPM2_STABLE PV
# Backlight seems different to i03
# What are gonio axis PVs as there are 2 PVs for Y, Z and only 1 for X
# S3 slits, are these same as S4 slits for I03? We only need these for deposition
# so perhaps we should refactor ispyb data collection to be more beamline-customisable
# Zocalo processing - CPU or GPU?
# Confirm no panda?
# PVs for turning on + off the thawer?
# Sample shutter, does this have the same arrangement with zebra for auto/manual control as for I03?


@devices.factory()
def baton() -> Baton:
    _baton = Baton(f"{PREFIX.beamline_prefix}-CS-BATON-01:")
    set_commissioning_signal(_baton.commissioning)
    return _baton


@devices.factory()
def xbpm_feedback(baton: Baton) -> XBPMFeedback:
    return XBPMFeedback(f"{PREFIX.beamline_prefix}-EA-FDBK-01:", baton=baton)


@devices.factory()
def attenuator() -> BinaryFilterAttenuator:
    return BinaryFilterAttenuator(
        prefix=f"{PREFIX.beamline_prefix}-OP-ATTN-01:",
        num_filters=8,
    )


@devices.factory(mock=True)
def aperture_scatterguard(config_client: ConfigClient) -> ApertureScatterguard:
    # TODO - implement beam sizing
    params = config_client.get_file_contents(BEAMLINE_PARAMETERS_PATH, dict)
    return ApertureScatterguard(
        aperture_prefix=f"{PREFIX.beamline_prefix}-MO-MAPT-01:",
        scatterguard_prefix=f"{PREFIX.beamline_prefix}-MO-SCAT-01:",
        loaded_positions=load_positions_from_beamline_parameters(params),
        tolerances=AperturePosition.tolerances_from_gda_params(params),
    )


@devices.factory(mock=True)
def backlight() -> Backlight:
    return Backlight(prefix=PREFIX.beamline_prefix)


@devices.factory()
def beamsize(aperture_scatterguard: ApertureScatterguard) -> Beamsize:
    # TODO - use correct implementation
    return Beamsize(aperture_scatterguard)


@devices.factory(mock=True)
def detector_motion() -> DetectorMotion:
    # TODO Simplify detector motion PVs
    return DetectorMotion(
        device_prefix=f"{PREFIX.beamline_prefix}-MO-DET-01:",
        pmac_prefix=f"{PREFIX.beamline_prefix}-MO-PMAC-02:",
    )


@devices.v1_init(
    EigerDetector, prefix=f"{PREFIX.beamline_prefix}-EA-EIGER-01:", wait=False
)
def eiger(eiger: EigerDetector) -> EigerDetector:
    eiger.detector_id = 78
    return eiger


@devices.factory()
def zebra_fast_grid_scan() -> ZebraFastGridScanThreeD:
    # TODO convert to different zebra fgs or update to newer controls
    # BL04J-MO-MD2-01:GONP:FGS:X_NUM_STEPS
    return ZebraFastGridScanThreeD(
        prefix=f"{PREFIX.beamline_prefix}-MO-MD2-01:GONP:",
    )


@devices.factory()
def flux() -> Flux:
    return Flux(f"{PREFIX.beamline_prefix}-MO-FLUX-01:")


@devices.factory()
def oav(
    config_client: ConfigClient,
    params: OAVConfigBeamCentre | None = None,
) -> OAVBeamCentreFile:
    return OAVBeamCentreFile(
        prefix=f"{PREFIX.beamline_prefix}-DI-OAV-01:",
        config=params
        or OAVConfigBeamCentre(ZOOM_PARAMS_FILE, DISPLAY_CONFIG, config_client),
    )


@devices.factory()
def pin_tip_detection() -> PinTipDetection:
    return PinTipDetection(f"{PREFIX.beamline_prefix}-DI-OAV-01:")


@devices.factory()
def gonio() -> XYZWrappedOmegaStage:
    # BL04J-MO-MD2-01:GONP:X.RBV
    # BL04J-MO-MD2-01:GONP:Y.RBV
    # BL04J-MO-MD2-01:GONP:Z.RBV
    # BL04J-MO-MD2-01:GONIO:OMEGA.RBV
    # BL04J-MO-MD2-01:GONIO:Y.RBV
    # BL04J-MO-MD2-01:GONIO:Z.RBV
    # TODO confirm axis PVs
    return XYZWrappedOmegaStage(f"{PREFIX.beamline_prefix}-MO-MD2-01:",
                                x_infix="GONP:X",
                                y_infix="GONP:Y",
                                z_infix="GONP:Y",
                                omega_infix="GONIO:OMEGA"
                                )

@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def s4_slit_gaps() -> MinimalSlits:
    # TODO rename these
    return MinimalSlits(
        f"{PREFIX.beamline_prefix}-AL-SLITS-03:", x_gap="XGAP", y_gap="YGAP"
    )


@devices.factory(mock=True)
def undulator(
        baton: Baton,
        daq_configuration_path: str,
        config_client: ConfigClient
) -> UndulatorInKeV:
    # TODO replace this with something much simpler
    return UndulatorInKeV(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        config_client=config_client,
        id_gap_lookup_table_path=f"{daq_configuration_path}/lookup/BeamLine_Undulator_toGap.txt",
        baton=baton,
    )


@devices.factory()
def zebra() -> Zebra:
    return Zebra(
        prefix=f"{PREFIX.beamline_prefix}-EA-ZEBRA-01:",
        mapping=I04_ZEBRA_MAPPING,
    )

@devices.factory()
def zocalo() -> ZocaloResults:
    return ZocaloResults(results_source=ZocaloSource.GPU)


@devices.factory()
def panda(panda_path_provider: PathProvider) -> HDFPanda:
    # TODO confirm remove this
    return HDFPanda(
        f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=panda_path_provider,
    )

@devices.factory()
def panda_fast_grid_scan() -> PandAFastGridScan:
    # TODO confirm remove this
    """This is used instead of the zebra_fast_grid_scan device when using the PandA."""
    return PandAFastGridScan(prefix=f"{PREFIX.beamline_prefix}-MO-SGON-01:")


@devices.factory(mock=True)
def thawer() -> Thawer:
    # TODO confirm whether we have control over this
    return Thawer(f"{PREFIX.beamline_prefix}-EA-THAW-01")


@devices.factory()
def sample_shutter() -> MXZebraShutter:
    return MXZebraShutter(f"{PREFIX.beamline_prefix}-EA-SHTR-01:")


@devices.factory(mock=True)
def vfm() -> FocusingMirrorWithStripes:
    # TODO remove this
    return FocusingMirrorWithStripes(
        prefix=f"{PREFIX.beamline_prefix}-OP-VFM-01:",
        bragg_to_lat_lut_path=DAQ_CONFIGURATION_PATH
        + "/lookup/BeamLineEnergy_DCM_VFM_x_converter.txt",
        x_suffix="LAT",
        y_suffix="VERT",
    )


@devices.factory(mock=True)
def mirror_voltages(config_client: ConfigClient) -> MirrorVoltages:
    # TODO remove this
    return MirrorVoltages(
        prefix=f"{PREFIX.beamline_prefix}-MO-PSU-01:",
        daq_configuration_path=DAQ_CONFIGURATION_PATH,
        config_client=config_client,
    )


@devices.factory(mock=True)
def dcm() -> DCM:
    # TODO remove this
    return DCM(prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:")


@devices.factory(mock=True)
def undulator_dcm(
    undulator: UndulatorInKeV,
    dcm: DCM,
    daq_configuration_path: str,
    config_client: ConfigClient,
) -> UndulatorDCM:
    # TODO remove this
    return UndulatorDCM(
        undulator=undulator,
        dcm=dcm,
        daq_configuration_path=daq_configuration_path,
        config_client=config_client,
    )


@devices.factory()
def robot() -> BartRobot:
    return BartRobot(f"{PREFIX.beamline_prefix}-MO-ROBOT-01:")


@devices.factory()
def webcam() -> Webcam:
    return Webcam(url=URL("http://i04-1-webcam1/axis-cgi/jpg/image.cgi"))


@devices.factory()
def lower_gonio() -> XYZStage:
    return XYZStage(f"{PREFIX.beamline_prefix}-MO-GONP-01:")


@devices.factory()
def beamstop(config_client: ConfigClient) -> Beamstop:
    return Beamstop(
        prefix=f"{PREFIX.beamline_prefix}-MO-BS-01:",
        beamline_parameters=config_client.get_file_contents(
            BEAMLINE_PARAMETERS_PATH, dict
        ),
    )


@devices.factory()
def collimation_table() -> CollimationTable:
    return CollimationTable(prefix=f"{PREFIX.beamline_prefix}-MO-COLP-01")


@devices.factory()
def cryostream() -> OxfordCryoStream:
    return OxfordCryoStream(f"{PREFIX.beamline_prefix}-EA-CSTRM-01:")


@devices.factory()
def cryojet() -> OxfordCryoJet:
    # TODO remove this
    return OxfordCryoJet(f"{PREFIX.beamline_prefix}-EA-CJET-01:")


@devices.factory(mock=True)
def cryostream_gantry() -> CryoStreamGantry:
    # TODO remove this
    return CryoStreamGantry(PREFIX.beamline_prefix)

