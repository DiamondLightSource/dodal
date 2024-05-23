from functools import partial
from unittest.mock import MagicMock, patch

import bluesky.plan_stubs as bps
import pytest
from ophyd.sim import NullStatus, make_fake_device
from ophyd_async.core import AsyncStatus, DeviceCollector, set_mock_value

from dodal.devices.aperturescatterguard import (
    TEST_APERTURE_POSITIONS,
    AperturePositions,
    ApertureScatterguard,
)
from dodal.devices.aperturescatterguard import get_mock_device as get_mock_ap_sg
from dodal.devices.backlight import Backlight
from dodal.devices.eiger import get_mock_device as get_mock_eiger
from dodal.devices.eiger_odin import EigerOdin
from dodal.devices.fast_grid_scan import get_mock_device as get_mock_fgs
from dodal.devices.flux import Flux
from dodal.devices.focusing_mirror import get_mock_voltages
from dodal.devices.i24.dual_backlight import DualBacklight
from dodal.devices.oav.oav_detector import get_mock_device as get_mock_oav
from dodal.devices.robot import get_mock_device as get_mock_bart_robot
from dodal.devices.slits import Slits
from dodal.devices.smargon import Smargon
from dodal.devices.synchrotron import get_mock_device as get_mock_synchrotron
from dodal.devices.undulator import Undulator
from dodal.devices.undulator_dcm import get_mock_device as get_mock_undulator_dcm
from dodal.devices.xspress3_mini.xspress3_mini import Xspress3Mini
from dodal.devices.zocalo.zocalo_results import ZOCALO_READING_PLAN_NAME, ZocaloResults
from dodal.testing_utils import constants

from .utility_functions import (
    create_new_detector_params,
    patch_ophyd_async_motor,
    patch_ophyd_motor,
)

ApSgAndLog = tuple[ApertureScatterguard, MagicMock]


@pytest.fixture
def test_aperture_positions():
    aperture_positions = AperturePositions.from_gda_beamline_params(
        TEST_APERTURE_POSITIONS
    )
    return aperture_positions


@pytest.fixture
async def mock_aperturescatterguard_with_call_log():
    call_log = MagicMock()
    ap_sg = await get_mock_ap_sg()
    with (
        patch_ophyd_async_motor(ap_sg.aperture.x, call_log=call_log),
        patch_ophyd_async_motor(ap_sg.aperture.y, call_log=call_log),
        patch_ophyd_async_motor(ap_sg.aperture.z, call_log=call_log),
        patch_ophyd_async_motor(ap_sg.scatterguard.x, call_log=call_log),
        patch_ophyd_async_motor(ap_sg.scatterguard.y, call_log=call_log),
    ):
        yield ap_sg, call_log


@pytest.fixture
async def mock_aperturescatterguard(
    mock_aperturescatterguard_with_call_log: ApSgAndLog,
):
    ap_sg, _ = mock_aperturescatterguard_with_call_log
    return ap_sg


@pytest.fixture
async def mock_aperturescatterguard_in_medium_pos_w_call_log(
    mock_aperturescatterguard_with_call_log: ApSgAndLog,
    test_aperture_positions: AperturePositions,
):
    ap_sg, call_log = mock_aperturescatterguard_with_call_log
    await ap_sg._set_raw_unsafe(test_aperture_positions.MEDIUM.location)
    set_mock_value(ap_sg.aperture.medium, 1)
    yield ap_sg, call_log


@pytest.fixture
async def mock_aperturescatterguard_in_medium_pos(
    mock_aperturescatterguard_in_medium_pos_w_call_log: ApSgAndLog,
):
    ap_sg, _ = mock_aperturescatterguard_in_medium_pos_w_call_log
    return ap_sg


@pytest.fixture
def mock_backlight(request: pytest.FixtureRequest) -> Backlight:
    return make_fake_device(Backlight)(name=f"backlight: {request.node.name}")


@pytest.fixture
async def mock_bart_robot():
    return await get_mock_bart_robot()


@pytest.fixture
def mock_dual_backlight(request: pytest.FixtureRequest) -> DualBacklight:
    return make_fake_device(DualBacklight)(name=f"backlight: {request.node.name}")


@pytest.fixture
def mock_eiger(request: pytest.FixtureRequest):
    yield get_mock_eiger(create_new_detector_params(), request.node.name)


@pytest.fixture
def mock_eiger_and_stage(mock_eiger):
    mock_eiger.stage = MagicMock(return_value=NullStatus())
    yield mock_eiger


@pytest.fixture
def mock_eiger_and_stage_unstage(mock_eiger_noop_stage):
    mock_eiger_noop_stage.unstage = MagicMock(return_value=NullStatus())
    yield mock_eiger_noop_stage


@pytest.fixture
def mock_fast_grid_scan(request: pytest.FixtureRequest):
    yield get_mock_fgs(request.node.name)


@pytest.fixture
def mock_flux(request: pytest.FixtureRequest):
    return make_fake_device(Flux)(name=f"flux: {request.node.name}")


@pytest.fixture
def mock_oav():
    yield get_mock_oav(constants.OAV_ZOOM_LEVELS, constants.OAV_DISPLAY_CONFIG)


@pytest.fixture
def mock_odin(request: pytest.FixtureRequest):
    return make_fake_device(EigerOdin)(name=f"eigerodin: {request.node.name}")


@pytest.fixture
async def mock_slits(request: pytest.FixtureRequest):
    async with DeviceCollector(mock=True):
        slits = Slits(f"slits: {request.node.name}")
    return slits


@pytest.fixture
def mock_smargon(request: pytest.FixtureRequest):
    smargon: Smargon = make_fake_device(Smargon)(name=f"smargon: {request.node.name}")
    smargon.x.user_setpoint._use_limits = False
    smargon.y.user_setpoint._use_limits = False
    smargon.z.user_setpoint._use_limits = False
    smargon.omega.user_setpoint._use_limits = False
    smargon.omega.velocity._use_limits = False
    with (
        patch_ophyd_motor(smargon.omega),
        patch_ophyd_motor(smargon.x),
        patch_ophyd_motor(smargon.y),
        patch_ophyd_motor(smargon.z),
        patch_ophyd_motor(smargon.chi),
        patch_ophyd_motor(smargon.phi),
    ):
        yield smargon


@pytest.fixture
async def mock_synchrotron():
    return await get_mock_synchrotron()


@pytest.fixture
def mock_vfm_mirror_voltages():
    return get_mock_voltages(constants.MOCK_DAQ_CONFIG_PATH)


@pytest.fixture
async def mock_undulator_dcm():
    return await get_mock_undulator_dcm(
        constants.ID_GAP_LOOKUP_TABLE_PATH, constants.MOCK_DAQ_CONFIG_PATH
    )


@pytest.fixture
async def mock_undulator() -> Undulator:
    async with DeviceCollector(mock=True):
        undulator = Undulator("UND-01", name="undulator")
    return undulator


@pytest.fixture
def mock_xspress3mini(request: pytest.FixtureRequest):
    return make_fake_device(Xspress3Mini)(name=f"xspress3mini: {request.node.name}")


@patch("dodal.devices.zocalo_results._get_zocalo_connection")
@pytest.fixture
async def get_mock_zocalo_device(RE):
    async def device(results, run_setup=False, mock_stage=False, mock_unstage=False):
        zd = ZocaloResults(zocalo_environment="test_env")

        @AsyncStatus.wrap
        async def mock_trigger(results):
            await zd._put_results(results, constants.ZOC_ISPYB_IDS)

        zd.trigger = MagicMock(side_effect=partial(mock_trigger, results))  # type: ignore
        await zd.connect()

        if run_setup:

            def plan():
                yield from bps.open_run()
                yield from bps.trigger_and_read([zd], name=ZOCALO_READING_PLAN_NAME)
                yield from bps.close_run()

            RE(plan())
        if mock_stage:
            zd.stage = MagicMock(return_value=NullStatus())  # type: ignore
        if mock_unstage:
            zd.unstage = MagicMock(return_value=NullStatus())  # type: ignore
        return zd

    return device
