from dataclasses import asdict
from typing import Sequence
from unittest.mock import call

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    assert_mock_put_called_with,
    set_mock_value,
)

from dodal.devices.aperturescatterguard import (
    ApertureFiveDimensionalLocation,
    AperturePositions,
    ApertureScatterguard,
    InvalidApertureMove,
    SingleAperturePosition,
)
from dodal.testing_utils import ApSgAndLog


def _assert_patched_ap_sg_has_call(
    ap_sg: ApertureScatterguard,
    position: ApertureFiveDimensionalLocation
    | tuple[float, float, float, float, float],
):
    for motor, pos in zip(
        (
            ap_sg.aperture.x,
            ap_sg.aperture.y,
            ap_sg.aperture.z,
            ap_sg.scatterguard.x,
            ap_sg.scatterguard.y,
        ),
        position,
    ):
        assert_mock_put_called_with(motor.user_setpoint, pos)


def test_aperture_scatterguard_rejects_unknown_position(
    mock_aperturescatterguard_in_medium_pos,
):
    position_to_reject = ApertureFiveDimensionalLocation(0, 0, 0, 0, 0)

    with pytest.raises(InvalidApertureMove):
        mock_aperturescatterguard_in_medium_pos.set(
            SingleAperturePosition("test", "GDA_NAME", 10, position_to_reject)
        )


def _call_list(calls: Sequence[float]):
    return [call(v, wait=True, timeout=10.0) for v in calls]


async def test_aperture_scatterguard_select_bottom_moves_sg_down_then_assembly_up(
    test_aperture_positions: AperturePositions,
    mock_aperturescatterguard_in_medium_pos_w_call_log: ApSgAndLog,
):
    ap_sg, call_log = mock_aperturescatterguard_in_medium_pos_w_call_log

    await ap_sg.set(test_aperture_positions.SMALL)

    call_log.assert_has_calls(_call_list((5.3375, -3.55, 2.43, 48.974, 15.8)))


async def test_aperture_unsafe_move(
    mock_aperturescatterguard_in_medium_pos: ApertureScatterguard,
):
    (a, b, c, d, e) = (0.2, 3.4, 5.6, 7.8, 9.0)
    ap_sg = mock_aperturescatterguard_in_medium_pos
    await ap_sg._set_raw_unsafe((a, b, c, d, e))  # type: ignore
    _assert_patched_ap_sg_has_call(ap_sg, (a, b, c, d, e))


async def test_aperture_scatterguard_select_top_moves_assembly_down_then_sg_up(
    test_aperture_positions: AperturePositions,
    mock_aperturescatterguard_in_medium_pos: ApertureScatterguard,
):
    ap_sg = mock_aperturescatterguard_in_medium_pos

    await ap_sg.set(test_aperture_positions.LARGE)

    _assert_patched_ap_sg_has_call(ap_sg, (2.389, 40.986, 15.8, 5.25, 4.43))


async def test_aperture_scatterguard_throws_error_if_outside_tolerance(
    mock_aperturescatterguard: ApertureScatterguard,
):
    ap_sg = mock_aperturescatterguard
    set_mock_value(ap_sg.aperture.z.deadband, 0.001)
    set_mock_value(ap_sg.aperture.z.user_readback, 1)
    set_mock_value(ap_sg.aperture.z.motor_done_move, 1)

    with pytest.raises(InvalidApertureMove):
        pos = ApertureFiveDimensionalLocation(0, 0, 1.1, 0, 0)
        await ap_sg._safe_move_within_datacollection_range(pos)


async def test_aperture_scatterguard_returns_status_if_within_tolerance(
    mock_aperturescatterguard: ApertureScatterguard,
):
    ap_sg = mock_aperturescatterguard
    set_mock_value(ap_sg.aperture.z.deadband, 0.001)
    set_mock_value(ap_sg.aperture.z.user_readback, 1)
    set_mock_value(ap_sg.aperture.z.motor_done_move, 1)

    pos = ApertureFiveDimensionalLocation(0, 0, 1, 0, 0)
    await ap_sg._safe_move_within_datacollection_range(pos)


def set_underlying_motors(
    mock_aperturescatterguard: ApertureScatterguard,
    position: ApertureFiveDimensionalLocation,
):
    mock_aperturescatterguard.aperture.x.set(position.aperture_x)
    mock_aperturescatterguard.aperture.y.set(position.aperture_y)
    mock_aperturescatterguard.aperture.z.set(position.aperture_z)
    mock_aperturescatterguard.scatterguard.x.set(position.scatterguard_x)
    mock_aperturescatterguard.scatterguard.y.set(position.scatterguard_y)


async def test_aperture_positions_large(
    mock_aperturescatterguard: ApertureScatterguard,
    test_aperture_positions: AperturePositions,
):
    set_mock_value(mock_aperturescatterguard.aperture.large, 1)
    assert (
        await mock_aperturescatterguard._get_current_aperture_position()
        == test_aperture_positions.LARGE
    )


async def test_aperture_positions_medium(
    mock_aperturescatterguard: ApertureScatterguard,
    test_aperture_positions: AperturePositions,
):
    set_mock_value(mock_aperturescatterguard.aperture.medium, 1)
    assert (
        await mock_aperturescatterguard._get_current_aperture_position()
        == test_aperture_positions.MEDIUM
    )


async def test_aperture_positions_small(
    mock_aperturescatterguard: ApertureScatterguard,
    test_aperture_positions: AperturePositions,
):
    set_mock_value(mock_aperturescatterguard.aperture.small, 1)
    assert (
        await mock_aperturescatterguard._get_current_aperture_position()
        == test_aperture_positions.SMALL
    )


async def test_aperture_positions_robot_load(
    mock_aperturescatterguard: ApertureScatterguard,
    test_aperture_positions: AperturePositions,
):
    set_mock_value(mock_aperturescatterguard.aperture.large, 0)
    set_mock_value(mock_aperturescatterguard.aperture.medium, 0)
    set_mock_value(mock_aperturescatterguard.aperture.small, 0)
    await mock_aperturescatterguard.aperture.y.set(
        test_aperture_positions.ROBOT_LOAD.location.aperture_y
    )
    assert (
        await mock_aperturescatterguard._get_current_aperture_position()
        == test_aperture_positions.ROBOT_LOAD
    )


async def test_aperture_positions_robot_load_within_tolerance(
    mock_aperturescatterguard: ApertureScatterguard,
    test_aperture_positions: AperturePositions,
):
    robot_load_ap_y = test_aperture_positions.ROBOT_LOAD.location.aperture_y
    tolerance = test_aperture_positions.tolerances.ap_y
    set_mock_value(mock_aperturescatterguard.aperture.large, 0)
    set_mock_value(mock_aperturescatterguard.aperture.medium, 0)
    set_mock_value(mock_aperturescatterguard.aperture.small, 0)
    await mock_aperturescatterguard.aperture.y.set(robot_load_ap_y + tolerance)
    assert (
        await mock_aperturescatterguard._get_current_aperture_position()
        == test_aperture_positions.ROBOT_LOAD
    )


async def test_aperture_positions_robot_load_outside_tolerance(
    mock_aperturescatterguard: ApertureScatterguard,
    test_aperture_positions: AperturePositions,
):
    robot_load_ap_y = test_aperture_positions.ROBOT_LOAD.location.aperture_y
    tolerance = test_aperture_positions.tolerances.ap_y + 0.01
    set_mock_value(mock_aperturescatterguard.aperture.large, 0)
    set_mock_value(mock_aperturescatterguard.aperture.medium, 0)
    set_mock_value(mock_aperturescatterguard.aperture.small, 0)
    await mock_aperturescatterguard.aperture.y.set(robot_load_ap_y + tolerance)
    with pytest.raises(InvalidApertureMove):
        await mock_aperturescatterguard._get_current_aperture_position()


async def test_aperture_positions_robot_load_unsafe(
    mock_aperturescatterguard: ApertureScatterguard,
    test_aperture_positions: AperturePositions,
):
    set_mock_value(mock_aperturescatterguard.aperture.large, 0)
    set_mock_value(mock_aperturescatterguard.aperture.medium, 0)
    set_mock_value(mock_aperturescatterguard.aperture.small, 0)
    await mock_aperturescatterguard.aperture.y.set(50.0)
    with pytest.raises(InvalidApertureMove):
        await mock_aperturescatterguard._get_current_aperture_position()


async def test_given_aperture_not_set_through_device_but_motors_in_position_when_device_read_then_position_returned(
    mock_aperturescatterguard_in_medium_pos: ApertureScatterguard,
    test_aperture_positions: AperturePositions,
):
    selected_aperture = await mock_aperturescatterguard_in_medium_pos.read()
    assert isinstance(selected_aperture, dict)
    assert selected_aperture["test_ap_sg-selected_aperture"]["value"] == asdict(
        test_aperture_positions.MEDIUM
    )


async def test_when_aperture_set_and_device_read_then_position_returned(
    mock_aperturescatterguard_in_medium_pos: ApertureScatterguard,
    test_aperture_positions: AperturePositions,
):
    await mock_aperturescatterguard_in_medium_pos.set(test_aperture_positions.MEDIUM)
    selected_aperture = await mock_aperturescatterguard_in_medium_pos.read()
    assert selected_aperture["test_ap_sg-selected_aperture"]["value"] == asdict(
        test_aperture_positions.MEDIUM
    )


async def test_ap_sg_in_runengine(
    mock_aperturescatterguard_in_medium_pos: ApertureScatterguard,
    RE: RunEngine,
):
    ap_sg = mock_aperturescatterguard_in_medium_pos
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
    mock_aperturescatterguard_in_medium_pos: ApertureScatterguard,
    RE: RunEngine,
):
    description = await mock_aperturescatterguard_in_medium_pos.describe()
    assert description
