from contextlib import ExitStack
from dataclasses import asdict
from typing import Sequence
from unittest.mock import ANY, MagicMock, call

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    get_mock_put,
    set_mock_value,
)

from dodal.devices.aperturescatterguard import (
    ApertureFiveDimensionalLocation,
    AperturePositionGDANames,
    AperturePositions,
    ApertureScatterguard,
    InvalidApertureMove,
    SingleAperturePosition,
)

from .conftest import patch_motor

ApSgAndLog = tuple[ApertureScatterguard, MagicMock]


def get_all_motors(ap_sg: ApertureScatterguard):
    return [
        ap_sg.aperture.x,
        ap_sg.aperture.y,
        ap_sg.aperture.z,
        ap_sg.scatterguard.x,
        ap_sg.scatterguard.y,
    ]


@pytest.fixture
async def ap_sg_and_call_log(aperture_positions: AperturePositions):
    call_log = MagicMock()
    ap_sg = ApertureScatterguard(name="test_ap_sg")
    await ap_sg.connect(mock=True)
    ap_sg.load_aperture_positions(aperture_positions)
    with ExitStack() as motor_patch_stack:
        for motor in get_all_motors(ap_sg):
            motor_patch_stack.enter_context(patch_motor(motor))
            call_log.attach_mock(get_mock_put(motor.user_setpoint), "setpoint")
        yield ap_sg, call_log


@pytest.fixture
async def ap_sg(ap_sg_and_call_log: ApSgAndLog):
    ap_sg, _ = ap_sg_and_call_log
    return ap_sg


@pytest.fixture
async def aperture_in_medium_pos_w_call_log(
    ap_sg_and_call_log: ApSgAndLog,
    aperture_positions: AperturePositions,
):
    ap_sg, call_log = ap_sg_and_call_log
    await ap_sg._set_raw_unsafe(aperture_positions.MEDIUM.location)

    set_mock_value(ap_sg.aperture.medium, 1)
    yield ap_sg, call_log


@pytest.fixture
async def aperture_in_medium_pos(aperture_in_medium_pos_w_call_log: ApSgAndLog):
    ap_sg, _ = aperture_in_medium_pos_w_call_log
    return ap_sg


@pytest.fixture
def aperture_positions():
    aperture_positions = AperturePositions.from_gda_beamline_params(
        {
            "miniap_x_LARGE_APERTURE": 2.389,
            "miniap_y_LARGE_APERTURE": 40.986,
            "miniap_z_LARGE_APERTURE": 15.8,
            "sg_x_LARGE_APERTURE": 5.25,
            "sg_y_LARGE_APERTURE": 4.43,
            "miniap_x_MEDIUM_APERTURE": 2.384,
            "miniap_y_MEDIUM_APERTURE": 44.967,
            "miniap_z_MEDIUM_APERTURE": 15.8,
            "sg_x_MEDIUM_APERTURE": 5.285,
            "sg_y_MEDIUM_APERTURE": 0.46,
            "miniap_x_SMALL_APERTURE": 2.430,
            "miniap_y_SMALL_APERTURE": 48.974,
            "miniap_z_SMALL_APERTURE": 15.8,
            "sg_x_SMALL_APERTURE": 5.3375,
            "sg_y_SMALL_APERTURE": -3.55,
            "miniap_x_ROBOT_LOAD": 2.386,
            "miniap_y_ROBOT_LOAD": 31.40,
            "miniap_z_ROBOT_LOAD": 15.8,
            "sg_x_ROBOT_LOAD": 5.25,
            "sg_y_ROBOT_LOAD": 4.43,
            "miniap_x_tolerance": 0.004,
            "miniap_y_tolerance": 0.1,
            "miniap_z_tolerance": 0.1,
            "sg_x_tolerance": 0.1,
            "sg_y_tolerance": 0.1,
        }
    )
    return aperture_positions


def _assert_patched_ap_sg_has_call(
    ap_sg: ApertureScatterguard,
    position: (
        ApertureFiveDimensionalLocation | tuple[float, float, float, float, float]
    ),
):
    for motor, pos in zip(
        get_all_motors(ap_sg),
        position,
    ):
        get_mock_put(motor.user_setpoint).assert_called_with(
            pos, wait=True, timeout=ANY
        )


def test_aperture_scatterguard_rejects_unknown_position(aperture_in_medium_pos):
    position_to_reject = ApertureFiveDimensionalLocation(0, 0, 0, 0, 0)

    with pytest.raises(InvalidApertureMove):
        aperture_in_medium_pos.set(
            SingleAperturePosition("test", "GDA_NAME", 10, position_to_reject)
        )


def _call_list(calls: Sequence[float]):
    return [call.setpoint(v, wait=True, timeout=ANY) for v in calls]


async def test_aperture_scatterguard_select_bottom_moves_sg_down_then_assembly_up(
    aperture_positions: AperturePositions,
    aperture_in_medium_pos_w_call_log: ApSgAndLog,
):
    ap_sg, call_log = aperture_in_medium_pos_w_call_log

    await ap_sg.set(aperture_positions.SMALL)

    call_log.assert_has_calls(_call_list((5.3375, -3.55, 2.43, 48.974, 15.8)))


async def test_aperture_unsafe_move(
    aperture_in_medium_pos: ApertureScatterguard,
):
    (a, b, c, d, e) = (0.2, 3.4, 5.6, 7.8, 9.0)
    ap_sg = aperture_in_medium_pos
    await ap_sg._set_raw_unsafe((a, b, c, d, e))  # type: ignore
    _assert_patched_ap_sg_has_call(ap_sg, (a, b, c, d, e))


async def test_aperture_scatterguard_select_top_moves_assembly_down_then_sg_up(
    aperture_positions: AperturePositions, aperture_in_medium_pos: ApertureScatterguard
):
    ap_sg = aperture_in_medium_pos

    await ap_sg.set(aperture_positions.LARGE)

    _assert_patched_ap_sg_has_call(ap_sg, (2.389, 40.986, 15.8, 5.25, 4.43))


async def test_aperture_scatterguard_throws_error_if_outside_tolerance(
    ap_sg: ApertureScatterguard,
):
    set_mock_value(ap_sg.aperture.z.deadband, 0.001)
    set_mock_value(ap_sg.aperture.z.user_readback, 1)
    set_mock_value(ap_sg.aperture.z.motor_done_move, 1)

    with pytest.raises(InvalidApertureMove):
        pos = ApertureFiveDimensionalLocation(0, 0, 1.1, 0, 0)
        await ap_sg._safe_move_within_datacollection_range(pos)


async def test_aperture_scatterguard_returns_status_if_within_tolerance(
    ap_sg: ApertureScatterguard,
):
    set_mock_value(ap_sg.aperture.z.deadband, 0.001)
    set_mock_value(ap_sg.aperture.z.user_readback, 1)
    set_mock_value(ap_sg.aperture.z.motor_done_move, 1)

    pos = ApertureFiveDimensionalLocation(0, 0, 1, 0, 0)
    await ap_sg._safe_move_within_datacollection_range(pos)


def set_underlying_motors(
    ap_sg: ApertureScatterguard, position: ApertureFiveDimensionalLocation
):
    for motor, pos in zip(
        get_all_motors(ap_sg),
        position,
    ):
        motor.set(pos)


async def test_aperture_positions_large(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    set_mock_value(ap_sg.aperture.large, 1)
    assert await ap_sg._get_current_aperture_position() == aperture_positions.LARGE


async def test_aperture_positions_medium(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    set_mock_value(ap_sg.aperture.medium, 1)
    assert await ap_sg._get_current_aperture_position() == aperture_positions.MEDIUM


async def test_aperture_positions_small(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    set_mock_value(ap_sg.aperture.small, 1)
    assert await ap_sg._get_current_aperture_position() == aperture_positions.SMALL


async def test_aperture_positions_robot_load(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    set_mock_value(ap_sg.aperture.large, 0)
    set_mock_value(ap_sg.aperture.medium, 0)
    set_mock_value(ap_sg.aperture.small, 0)
    await ap_sg.aperture.y.set(aperture_positions.ROBOT_LOAD.location.aperture_y)
    assert await ap_sg._get_current_aperture_position() == aperture_positions.ROBOT_LOAD


async def test_aperture_positions_robot_load_within_tolerance(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    robot_load_ap_y = aperture_positions.ROBOT_LOAD.location.aperture_y
    tolerance = aperture_positions.tolerances.ap_y
    set_mock_value(ap_sg.aperture.large, 0)
    set_mock_value(ap_sg.aperture.medium, 0)
    set_mock_value(ap_sg.aperture.small, 0)
    await ap_sg.aperture.y.set(robot_load_ap_y + tolerance)
    assert await ap_sg._get_current_aperture_position() == aperture_positions.ROBOT_LOAD


async def test_aperture_positions_robot_load_outside_tolerance(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    robot_load_ap_y = aperture_positions.ROBOT_LOAD.location.aperture_y
    tolerance = aperture_positions.tolerances.ap_y + 0.01
    set_mock_value(ap_sg.aperture.large, 0)
    set_mock_value(ap_sg.aperture.medium, 0)
    set_mock_value(ap_sg.aperture.small, 0)
    await ap_sg.aperture.y.set(robot_load_ap_y + tolerance)
    with pytest.raises(InvalidApertureMove):
        await ap_sg._get_current_aperture_position()


async def test_aperture_positions_robot_load_unsafe(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    set_mock_value(ap_sg.aperture.large, 0)
    set_mock_value(ap_sg.aperture.medium, 0)
    set_mock_value(ap_sg.aperture.small, 0)
    await ap_sg.aperture.y.set(50.0)
    with pytest.raises(InvalidApertureMove):
        await ap_sg._get_current_aperture_position()


async def test_given_aperture_not_set_through_device_but_motors_in_position_when_device_read_then_position_returned(
    aperture_in_medium_pos: ApertureScatterguard, aperture_positions: AperturePositions
):
    selected_aperture = await aperture_in_medium_pos.read()
    assert isinstance(selected_aperture, dict)
    assert selected_aperture["test_ap_sg-selected_aperture"]["value"] == asdict(
        aperture_positions.MEDIUM
    )


async def test_when_aperture_set_and_device_read_then_position_returned(
    aperture_in_medium_pos: ApertureScatterguard, aperture_positions: AperturePositions
):
    await aperture_in_medium_pos.set(aperture_positions.MEDIUM)
    selected_aperture = await aperture_in_medium_pos.read()
    assert selected_aperture["test_ap_sg-selected_aperture"]["value"] == asdict(
        aperture_positions.MEDIUM
    )


async def test_ap_sg_in_runengine(
    aperture_in_medium_pos: ApertureScatterguard,
    RE: RunEngine,
):
    ap_sg = aperture_in_medium_pos
    ap = ap_sg.aperture
    sg = ap_sg.scatterguard
    assert ap_sg.aperture_positions
    test_position = ap_sg.aperture_positions.SMALL
    test_loc = test_position.location
    RE(bps.abs_set(ap_sg, test_position, wait=True))
    assert await ap.x.user_readback.get_value() == test_loc.aperture_x
    assert await ap.y.user_readback.get_value() == test_loc.aperture_y
    assert await ap.z.user_readback.get_value() == test_loc.aperture_z
    assert await sg.x.user_readback.get_value() == test_loc.scatterguard_x
    assert await sg.y.user_readback.get_value() == test_loc.scatterguard_y


async def test_ap_sg_descriptor(
    aperture_in_medium_pos: ApertureScatterguard,
    RE: RunEngine,
):
    description = await aperture_in_medium_pos.describe()
    assert description


def test_get_position_from_gda_aperture_name(
    RE: RunEngine, aperture_positions: AperturePositions
):
    assert (
        aperture_positions.get_position_from_gda_aperture_name(
            AperturePositionGDANames.LARGE_APERTURE
        )
        == aperture_positions.LARGE
    )
    assert (
        aperture_positions.get_position_from_gda_aperture_name(
            AperturePositionGDANames.MEDIUM_APERTURE
        )
        == aperture_positions.MEDIUM
    )
    assert (
        aperture_positions.get_position_from_gda_aperture_name(
            AperturePositionGDANames.SMALL_APERTURE
        )
        == aperture_positions.SMALL
    )
    assert (
        aperture_positions.get_position_from_gda_aperture_name(
            AperturePositionGDANames.ROBOT_LOAD
        )
        == aperture_positions.ROBOT_LOAD
    )
    with pytest.raises(ValueError):
        aperture_positions.get_position_from_gda_aperture_name(
            "VERY TINY APERTURE"  # type: ignore
        )
