import asyncio
from collections.abc import Sequence
from contextlib import ExitStack
from typing import Any
from unittest.mock import AsyncMock, MagicMock, call

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.aperturescatterguard import (
    AperturePosition,
    ApertureScatterguard,
    ApertureValue,
    InvalidApertureMove,
    load_positions_from_beamline_parameters,
)
from dodal.devices.util.test_utils import patch_motor

ApSgAndLog = tuple[ApertureScatterguard, MagicMock]


@pytest.fixture
def aperture_positions() -> dict[ApertureValue, AperturePosition]:
    return load_positions_from_beamline_parameters(
        GDABeamlineParameters(
            params={
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
            }
        )
    )


@pytest.fixture
def aperture_tolerances():
    return AperturePosition.tolerances_from_gda_params(
        GDABeamlineParameters(
            {
                "miniap_x_tolerance": 0.004,
                "miniap_y_tolerance": 0.1,
                "miniap_z_tolerance": 0.1,
                "sg_x_tolerance": 0.1,
                "sg_y_tolerance": 0.1,
            }
        )
    )


def get_all_motors(ap_sg: ApertureScatterguard):
    return [
        ap_sg.aperture.x,
        ap_sg.aperture.y,
        ap_sg.aperture.z,
        ap_sg.scatterguard.x,
        ap_sg.scatterguard.y,
    ]


@pytest.fixture
async def ap_sg_and_call_log(
    RE: RunEngine,
    aperture_positions: dict[ApertureValue, AperturePosition],
    aperture_tolerances: AperturePosition,
):
    call_log = MagicMock()
    async with init_devices(mock=True):
        ap_sg = ApertureScatterguard(
            name="test_ap_sg",
            loaded_positions=aperture_positions,
            tolerances=aperture_tolerances,
        )
    with ExitStack() as motor_patch_stack:
        for motor in get_all_motors(ap_sg):
            motor_patch_stack.enter_context(patch_motor(motor))
            call_log.attach_mock(get_mock_put(motor.user_setpoint), "setpoint")
        yield ap_sg, call_log


@pytest.fixture
async def ap_sg(ap_sg_and_call_log: ApSgAndLog):
    ap_sg, _ = ap_sg_and_call_log
    return ap_sg


async def set_to_position(
    aperture_scatterguard: ApertureScatterguard, position: AperturePosition
):
    aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = position.values

    await asyncio.gather(
        aperture_scatterguard.aperture.x.set(aperture_x),
        aperture_scatterguard.aperture.y.set(aperture_y),
        aperture_scatterguard.aperture.z.set(aperture_z),
        aperture_scatterguard.scatterguard.x.set(scatterguard_x),
        aperture_scatterguard.scatterguard.y.set(scatterguard_y),
    )


@pytest.fixture
async def aperture_in_medium_pos_w_call_log(
    ap_sg_and_call_log: ApSgAndLog,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    ap_sg, call_log = ap_sg_and_call_log
    await set_to_position(ap_sg, aperture_positions[ApertureValue.MEDIUM])

    set_mock_value(ap_sg.aperture.medium, 1)

    yield ap_sg, call_log


@pytest.fixture
async def aperture_in_medium_pos(aperture_in_medium_pos_w_call_log: ApSgAndLog):
    ap_sg, _ = aperture_in_medium_pos_w_call_log
    return ap_sg


def _assert_patched_ap_sg_has_call(
    ap_sg: ApertureScatterguard,
    position: AperturePosition,
):
    for motor, pos in zip(
        get_all_motors(ap_sg),
        position.values,
        strict=False,
    ):
        get_mock_put(motor.user_setpoint).assert_called_with(pos, wait=True)


def _assert_position_in_reading(
    reading: dict[str, Any],
    aperture: ApertureValue,
    position: AperturePosition,
    device_name: str,
):
    assert reading[f"{device_name}-aperture-x"]["value"] == position.aperture_x
    assert reading[f"{device_name}-aperture-y"]["value"] == position.aperture_y
    assert reading[f"{device_name}-aperture-z"]["value"] == position.aperture_z
    assert reading[f"{device_name}-scatterguard-x"]["value"] == position.scatterguard_x
    assert reading[f"{device_name}-scatterguard-y"]["value"] == position.scatterguard_y


def _call_list(calls: Sequence[float]):
    return [call.setpoint(v, wait=True) for v in calls]


async def test_aperture_scatterguard_select_bottom_moves_sg_down_then_assembly_up(
    aperture_in_medium_pos_w_call_log: ApSgAndLog,
):
    ap_sg, call_log = aperture_in_medium_pos_w_call_log

    await ap_sg.selected_aperture.set(ApertureValue.SMALL)

    call_log.assert_has_calls(_call_list((5.3375, -3.55, 2.43, 48.974, 15.8)))


async def test_aperture_unsafe_move(
    aperture_in_medium_pos: ApertureScatterguard,
):
    pos = AperturePosition(
        aperture_x=0.2,
        aperture_y=3.4,
        aperture_z=5.6,
        scatterguard_x=7.8,
        scatterguard_y=9.0,
        radius=0,
    )
    ap_sg = aperture_in_medium_pos
    await ap_sg._set_raw_unsafe(pos)
    _assert_patched_ap_sg_has_call(ap_sg, pos)


async def test_aperture_scatterguard_select_top_moves_assembly_down_then_sg_up(
    aperture_in_medium_pos: ApertureScatterguard,
):
    ap_sg = aperture_in_medium_pos

    await ap_sg.selected_aperture.set(ApertureValue.LARGE)

    _assert_patched_ap_sg_has_call(
        ap_sg,
        AperturePosition(
            aperture_x=2.389,
            aperture_y=40.986,
            aperture_z=15.8,
            scatterguard_x=5.25,
            scatterguard_y=4.43,
            radius=100,
        ),
    )


@pytest.mark.parametrize(
    "selected_aperture",
    [
        ApertureValue.SMALL,
        ApertureValue.MEDIUM,
        ApertureValue.LARGE,
        ApertureValue.OUT_OF_BEAM,
    ],
)
async def test_given_aperture_z_still_moving_when_aperture_scatterguard_moved_then_raises(
    selected_aperture: ApertureValue,
    ap_sg: ApertureScatterguard,
):
    set_mock_value(ap_sg.aperture.z.motor_done_move, 0)
    with pytest.raises(InvalidApertureMove):
        await ap_sg.selected_aperture.set(selected_aperture)


@pytest.mark.parametrize(
    "selected_aperture",
    [
        ApertureValue.SMALL,
        ApertureValue.MEDIUM,
        ApertureValue.LARGE,
        ApertureValue.OUT_OF_BEAM,
    ],
)
async def test_aperture_scatterguard_throws_error_if_z_outside_tolerance(
    selected_aperture: ApertureValue,
    ap_sg: ApertureScatterguard,
):
    set_mock_value(ap_sg.aperture.z.user_readback, 1)
    set_mock_value(ap_sg.aperture.z.motor_done_move, 1)

    with pytest.raises(InvalidApertureMove):
        await ap_sg.selected_aperture.set(selected_aperture)


async def test_aperture_scatterguard_returns_status_if_within_tolerance(
    ap_sg: ApertureScatterguard,
):
    set_mock_value(ap_sg.aperture.z.user_readback, 1)
    set_mock_value(ap_sg.aperture.z.motor_done_move, 1)

    pos = AperturePosition(
        aperture_x=0, aperture_y=0, aperture_z=1, scatterguard_x=0, scatterguard_y=0
    )
    await ap_sg._safe_move_whilst_in_beam(pos)


def set_underlying_motors(ap_sg: ApertureScatterguard, position: AperturePosition):
    for motor, pos in zip(
        get_all_motors(ap_sg),
        position.values,
        strict=False,
    ):
        motor.set(pos)


@pytest.mark.parametrize(
    "read_pv, aperture",
    [
        ("large", ApertureValue.LARGE),
        ("medium", ApertureValue.MEDIUM),
        ("small", ApertureValue.SMALL),
    ],
)
async def test_aperture_positions(
    ap_sg: ApertureScatterguard,
    aperture_positions: dict[ApertureValue, AperturePosition],
    read_pv: str,
    aperture: ApertureValue,
):
    set_mock_value(getattr(ap_sg.aperture, read_pv), 1)
    reading = await ap_sg.read()
    assert isinstance(reading, dict)
    assert (
        reading[f"{ap_sg.name}-radius"]["value"] == aperture_positions[aperture].radius
    )
    assert reading[f"{ap_sg.name}-selected_aperture"]["value"] == aperture


async def test_aperture_positions_robot_load(
    ap_sg: ApertureScatterguard,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    set_mock_value(ap_sg.aperture.large, 0)
    set_mock_value(ap_sg.aperture.medium, 0)
    set_mock_value(ap_sg.aperture.small, 0)
    robot_load = aperture_positions[ApertureValue.OUT_OF_BEAM]
    await ap_sg.aperture.y.set(robot_load.aperture_y)
    reading = await ap_sg.read()
    assert isinstance(reading, dict)
    assert reading[f"{ap_sg.name}-radius"]["value"] == 0.0
    assert (
        reading[f"{ap_sg.name}-selected_aperture"]["value"] == ApertureValue.OUT_OF_BEAM
    )


async def test_aperture_positions_robot_load_within_tolerance(
    ap_sg: ApertureScatterguard,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    robot_load = aperture_positions[ApertureValue.OUT_OF_BEAM]
    robot_load_ap_y = robot_load.aperture_y
    tolerance = ap_sg._tolerances.aperture_y
    set_mock_value(ap_sg.aperture.large, 0)
    set_mock_value(ap_sg.aperture.medium, 0)
    set_mock_value(ap_sg.aperture.small, 0)
    await ap_sg.aperture.y.set(robot_load_ap_y + tolerance)
    reading = await ap_sg.read()
    assert isinstance(reading, dict)
    assert reading[f"{ap_sg.name}-radius"]["value"] == 0.0
    assert (
        reading[f"{ap_sg.name}-selected_aperture"]["value"] == ApertureValue.OUT_OF_BEAM
    )


async def test_aperture_positions_robot_load_outside_tolerance(
    ap_sg: ApertureScatterguard,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    robot_load = aperture_positions[ApertureValue.OUT_OF_BEAM]
    robot_load_ap_y = robot_load.aperture_y
    tolerance = ap_sg._tolerances.aperture_y + 0.01
    set_mock_value(ap_sg.aperture.large, 0)
    set_mock_value(ap_sg.aperture.medium, 0)
    set_mock_value(ap_sg.aperture.small, 0)
    await ap_sg.aperture.y.set(robot_load_ap_y + tolerance)
    with pytest.raises(InvalidApertureMove):
        await ap_sg.read()


async def test_aperture_positions_robot_load_unsafe(
    ap_sg: ApertureScatterguard,
):
    set_mock_value(ap_sg.aperture.large, 0)
    set_mock_value(ap_sg.aperture.medium, 0)
    set_mock_value(ap_sg.aperture.small, 0)
    await ap_sg.aperture.y.set(50.0)
    with pytest.raises(InvalidApertureMove):
        await ap_sg.read()


async def test_given_aperture_not_set_through_device_but_motors_in_position_when_device_read_then_position_returned(
    aperture_in_medium_pos: ApertureScatterguard,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    reading = await aperture_in_medium_pos.read()
    assert isinstance(reading, dict)
    _assert_position_in_reading(
        reading,
        ApertureValue.MEDIUM,
        aperture_positions[ApertureValue.MEDIUM],
        aperture_in_medium_pos.name,
    )


@pytest.mark.parametrize(
    "aperture",
    [
        ApertureValue.SMALL,
        ApertureValue.MEDIUM,
        ApertureValue.LARGE,
    ],
)
async def test_when_aperture_set_and_device_read_then_position_returned(
    aperture: ApertureValue,
    aperture_in_medium_pos: ApertureScatterguard,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    await aperture_in_medium_pos.selected_aperture.set(aperture)
    reading = await aperture_in_medium_pos.read()
    _assert_position_in_reading(
        reading,
        aperture,
        aperture_positions[aperture],
        aperture_in_medium_pos.name,
    )


async def test_ap_sg_in_runengine(
    aperture_in_medium_pos: ApertureScatterguard,
    RE: RunEngine,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    ap = aperture_in_medium_pos.aperture
    sg = aperture_in_medium_pos.scatterguard
    test_loc = aperture_positions[ApertureValue.SMALL]

    def set_small_readback_pv(value, *args, **kwargs):
        set_mock_value(ap.small, 1)
        set_mock_value(ap.medium, 0)
        set_mock_value(ap.y.user_readback, value)

    callback_on_mock_put(ap.y.user_setpoint, set_small_readback_pv)

    RE(
        bps.abs_set(
            aperture_in_medium_pos.selected_aperture, ApertureValue.SMALL, wait=True
        )
    )
    assert await ap.x.user_readback.get_value() == test_loc.aperture_x
    assert await ap.y.user_readback.get_value() == test_loc.aperture_y
    assert await ap.z.user_readback.get_value() == test_loc.aperture_z
    assert await sg.x.user_readback.get_value() == test_loc.scatterguard_x
    assert await sg.y.user_readback.get_value() == test_loc.scatterguard_y
    assert (
        await aperture_in_medium_pos.selected_aperture.get_value()
        == ApertureValue.SMALL
    )
    assert await aperture_in_medium_pos.radius.get_value() == 20


async def test_ap_sg_descriptor(
    aperture_in_medium_pos: ApertureScatterguard,
):
    description = await aperture_in_medium_pos.describe()
    assert description


async def assert_all_positions_other_than_y(
    ap_sg: ApertureScatterguard, position: AperturePosition
):
    ap = ap_sg.aperture
    sg = ap_sg.scatterguard
    assert await ap.x.user_setpoint.get_value() == position.aperture_x
    assert await ap.z.user_setpoint.get_value() == position.aperture_z
    assert await sg.x.user_setpoint.get_value() == position.scatterguard_x
    assert await sg.y.user_setpoint.get_value() == position.scatterguard_y


async def test_given_aperture_out_when_new_aperture_selected_then_aperture_not_moved_in(
    ap_sg: ApertureScatterguard,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    ap = ap_sg.aperture
    y_set_point = aperture_positions[ApertureValue.OUT_OF_BEAM].aperture_y
    ap.y.set(y_set_point)
    set_mock_value(ap.y.user_readback, y_set_point)

    await ap_sg.prepare(ApertureValue.SMALL)
    assert await ap.y.user_setpoint.get_value() == y_set_point

    await assert_all_positions_other_than_y(
        ap_sg, aperture_positions[ApertureValue.SMALL]
    )


async def test_given_aperture_in_when_new_aperture_set_then_aperture_moved_safely(
    aperture_in_medium_pos: ApertureScatterguard,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    aperture_in_medium_pos._safe_move_whilst_in_beam = AsyncMock()
    await aperture_in_medium_pos.prepare(ApertureValue.SMALL)
    aperture_in_medium_pos._safe_move_whilst_in_beam.assert_called_once_with(
        aperture_positions[ApertureValue.SMALL]
    )


@pytest.mark.parametrize(
    "selected_aperture",
    [ApertureValue.SMALL, ApertureValue.MEDIUM, ApertureValue.LARGE],
)
async def test_given_in_and_aperture_selected_when_move_out_then_only_aperture_y_moves(
    selected_aperture: ApertureValue,
    ap_sg: ApertureScatterguard,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    y_setpoint = ap_sg.aperture.y.user_setpoint
    aperture_position = aperture_positions[selected_aperture]
    await set_to_position(ap_sg, aperture_position)

    assert await y_setpoint.get_value() == aperture_position.aperture_y

    await ap_sg.selected_aperture.set(ApertureValue.OUT_OF_BEAM)
    await assert_all_positions_other_than_y(ap_sg, aperture_position)

    assert (
        await y_setpoint.get_value()
        == aperture_positions[ApertureValue.OUT_OF_BEAM].aperture_y
    )


@pytest.mark.parametrize(
    "selected_aperture",
    [ApertureValue.SMALL, ApertureValue.MEDIUM, ApertureValue.LARGE],
)
async def test_given_out_and_aperture_selected_when_move_in_then_correct_y_selected(
    selected_aperture: ApertureValue,
    ap_sg: ApertureScatterguard,
    aperture_positions: dict[ApertureValue, AperturePosition],
):
    y_setpoint = ap_sg.aperture.y.user_setpoint
    aperture_position = aperture_positions[selected_aperture]
    set_mock_value(ap_sg.aperture.z.user_readback, aperture_position.aperture_z)
    await ap_sg.selected_aperture.set(ApertureValue.OUT_OF_BEAM)

    await ap_sg.prepare(selected_aperture)

    await ap_sg.selected_aperture.set(selected_aperture)
    await assert_all_positions_other_than_y(ap_sg, aperture_position)
    assert await y_setpoint.get_value() == aperture_position.aperture_y


def test_aperture_enum_name_formatting():
    assert f"{ApertureValue.SMALL}" == "Small"
    assert f"{ApertureValue.MEDIUM}" == "Medium"
    assert f"{ApertureValue.LARGE}" == "Large"
    assert f"{ApertureValue.OUT_OF_BEAM}" == "Out_of_beam"


async def test_calling_prepare_then_set_in_quick_succession_throws_an_error(
    ap_sg: ApertureScatterguard,
):
    async def set_motor_moving(value, *args, **kwargs):
        set_mock_value(ap_sg.aperture.x.motor_done_move, 0)

    callback_on_mock_put(ap_sg.aperture.x.user_setpoint, set_motor_moving)
    await ap_sg.prepare(ApertureValue.SMALL)

    with pytest.raises(InvalidApertureMove):
        await ap_sg.selected_aperture.set(ApertureValue.SMALL)
