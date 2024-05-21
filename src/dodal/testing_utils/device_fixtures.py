from unittest.mock import MagicMock

import pytest
from ophyd.sim import make_fake_device
from ophyd_async.core import set_mock_value

from dodal.devices.aperturescatterguard import (
    TEST_APERTURE_POSITIONS,
    AperturePositions,
    ApertureScatterguard,
)
from dodal.devices.aperturescatterguard import get_mock_device as get_mock_ap_sg
from dodal.devices.backlight import Backlight
from dodal.devices.eiger import get_mock_eiger
from dodal.devices.fast_grid_scan import make_mock_device as make_mock_fgs
from dodal.devices.focusing_mirror import get_mock_voltages
from dodal.devices.i24.dual_backlight import DualBacklight
from dodal.devices.robot import get_mock_device as get_mock_bart_robot
from dodal.devices.smargon import Smargon
from dodal.devices.undulator_dcm import get_mock_device as get_mock_undulator_dcm

from .constants import (
    ID_GAP_LOOKUP_TABLE_PATH,
    MOCK_DAQ_CONFIG_PATH,
)
from .utility_functions import create_new_detector_params, patch_ophyd_async_motor

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
def mock_fast_grid_scan(request: pytest.FixtureRequest):
    yield make_mock_fgs(request.node.name)


@pytest.fixture
def mock_smargon(request: pytest.FixtureRequest) -> Smargon:
    return make_fake_device(Smargon)(name=f"smargon: {request.node.name}")


@pytest.fixture
def mock_vfm_mirror_voltages():
    return get_mock_voltages(MOCK_DAQ_CONFIG_PATH)


@pytest.fixture
async def mock_undulator_dcm():
    return await get_mock_undulator_dcm(ID_GAP_LOOKUP_TABLE_PATH, MOCK_DAQ_CONFIG_PATH)
