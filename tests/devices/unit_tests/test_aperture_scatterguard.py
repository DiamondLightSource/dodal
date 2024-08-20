from collections.abc import Sequence
from contextlib import ExitStack
from dataclasses import asdict
from unittest.mock import ANY, MagicMock, call

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    DeviceCollector,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.aperturescatterguard import (
    ApertureFiveDimensionalLocation,
    ApertureInOut,
    AperturePosition,
    AperturePositionGDANames,
    ApertureScatterguard,
    ApertureScatterguardTolerances,
    InvalidApertureMove,
    SingleAperturePosition,
    load_positions_from_beamline_parameters,
    load_tolerances_from_beamline_params,
)
from dodal.devices.util.test_utils import patch_motor

ApSgAndLog = tuple[ApertureScatterguard, MagicMock]


@pytest.fixture
def aperture_positions() -> dict[AperturePosition, SingleAperturePosition]:
    return load_positions_from_beamline_parameters(
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
        }  # type:ignore
    )


@pytest.fixture
def aperture_tolerances():
    return load_tolerances_from_beamline_params(
        {
            "miniap_x_tolerance": 0.004,
            "miniap_y_tolerance": 0.1,
            "miniap_z_tolerance": 0.1,
            "sg_x_tolerance": 0.1,
            "sg_y_tolerance": 0.1,
        }  # type:ignore
    )


def get_all_motors(ap_sg: ApertureScatterguard):
    return [
        ap_sg._aperture.x,
        ap_sg._aperture.y,
        ap_sg._aperture.z,
        ap_sg._scatterguard.x,
        ap_sg._scatterguard.y,
    ]


@pytest.fixture
async def ap_sg_and_call_log(
    RE: RunEngine,
    aperture_positions: dict[AperturePosition, SingleAperturePosition],
    aperture_tolerances: ApertureScatterguardTolerances,
):
    call_log = MagicMock()
    async with DeviceCollector(mock=True):
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


@pytest.fixture
async def aperture_in_medium_pos_w_call_log(
    ap_sg_and_call_log: ApSgAndLog,
    aperture_positions: dict[AperturePosition, SingleAperturePosition],
):
    ap_sg, call_log = ap_sg_and_call_log
    await ap_sg._set_raw_unsafe(aperture_positions[AperturePosition.MEDIUM].location)

    set_mock_value(ap_sg._aperture.medium, 1)
    yield ap_sg, call_log


@pytest.fixture
async def aperture_in_medium_pos(aperture_in_medium_pos_w_call_log: ApSgAndLog):
    ap_sg, _ = aperture_in_medium_pos_w_call_log
    return ap_sg


def _assert_patched_ap_sg_has_call(
    ap_sg: ApertureScatterguard,
    position: (
        ApertureFiveDimensionalLocation | tuple[float, float, float, float, float]
    ),
):
    for motor, pos in zip(
        get_all_motors(ap_sg),
        position,
        strict=False,
    ):
        get_mock_put(motor.user_setpoint).assert_called_with(
            pos, wait=True, timeout=ANY
        )


def _call_list(calls: Sequence[float]):
    return [call.setpoint(v, wait=True, timeout=ANY) for v in calls]


async def test_aperture_scatterguard_select_bottom_moves_sg_down_then_assembly_up(
    aperture_in_medium_pos_w_call_log: ApSgAndLog,
):
    ap_sg, call_log = aperture_in_medium_pos_w_call_log

    await ap_sg.set((ApertureInOut.IN, AperturePosition.SMALL))

    call_log.assert_has_calls(_call_list((5.3375, -3.55, 2.43, 48.974, 15.8)))


async def test_aperture_unsafe_move(
    aperture_in_medium_pos: ApertureScatterguard,
):
    (a, b, c, d, e) = (0.2, 3.4, 5.6, 7.8, 9.0)
    ap_sg = aperture_in_medium_pos
    await ap_sg._set_raw_unsafe((a, b, c, d, e))  # type: ignore
    _assert_patched_ap_sg_has_call(ap_sg, (a, b, c, d, e))


async def test_aperture_scatterguard_select_top_moves_assembly_down_then_sg_up(
    aperture_in_medium_pos: ApertureScatterguard,
):
    ap_sg = aperture_in_medium_pos

    await ap_sg.set((ApertureInOut.IN, AperturePosition.LARGE))

    _assert_patched_ap_sg_has_call(ap_sg, (2.389, 40.986, 15.8, 5.25, 4.43))


async def test_aperture_scatterguard_throws_error_if_outside_tolerance(
    ap_sg: ApertureScatterguard,
):
    set_mock_value(ap_sg._aperture.z.deadband, 0.001)
    set_mock_value(ap_sg._aperture.z.user_readback, 1)
    set_mock_value(ap_sg._aperture.z.motor_done_move, 1)

    with pytest.raises(InvalidApertureMove):
        pos = ApertureFiveDimensionalLocation(0, 0, 1.1, 0, 0)
        await ap_sg._safe_move_within_datacollection_range(pos)


async def test_aperture_scatterguard_returns_status_if_within_tolerance(
    ap_sg: ApertureScatterguard,
):
    set_mock_value(ap_sg._aperture.z.deadband, 0.001)
    set_mock_value(ap_sg._aperture.z.user_readback, 1)
    set_mock_value(ap_sg._aperture.z.motor_done_move, 1)

    pos = ApertureFiveDimensionalLocation(0, 0, 1, 0, 0)
    await ap_sg._safe_move_within_datacollection_range(pos)


def set_underlying_motors(
    ap_sg: ApertureScatterguard, position: ApertureFiveDimensionalLocation
):
    for motor, pos in zip(
        get_all_motors(ap_sg),
        position,
        strict=False,
    ):
        motor.set(pos)


async def test_aperture_positions_large(
    ap_sg: ApertureScatterguard, aperture_positions
):
    set_mock_value(ap_sg._aperture.large, 1)
    assert (
        await ap_sg.get_current_aperture_position()
        == aperture_positions[AperturePosition.LARGE]
    )


async def test_aperture_positions_medium(
    ap_sg: ApertureScatterguard, aperture_positions
):
    set_mock_value(ap_sg._aperture.medium, 1)
    assert (
        await ap_sg.get_current_aperture_position()
        == aperture_positions[AperturePosition.MEDIUM]
    )


async def test_aperture_positions_small(
    ap_sg: ApertureScatterguard, aperture_positions
):
    set_mock_value(ap_sg._aperture.small, 1)
    assert (
        await ap_sg.get_current_aperture_position()
        == aperture_positions[AperturePosition.SMALL]
    )


async def test_aperture_positions_robot_load(
    ap_sg: ApertureScatterguard,
    aperture_positions: dict[AperturePosition, SingleAperturePosition],
):
    set_mock_value(ap_sg._aperture.large, 0)
    set_mock_value(ap_sg._aperture.medium, 0)
    set_mock_value(ap_sg._aperture.small, 0)
    robot_load = aperture_positions[AperturePosition.ROBOT_LOAD]
    await ap_sg._aperture.y.set(robot_load.location.aperture_y)
    assert await ap_sg.get_current_aperture_position() == robot_load


async def test_aperture_positions_robot_load_within_tolerance(
    ap_sg: ApertureScatterguard,
    aperture_positions: dict[AperturePosition, SingleAperturePosition],
):
    robot_load = aperture_positions[AperturePosition.ROBOT_LOAD]
    robot_load_ap_y = robot_load.location.aperture_y
    tolerance = ap_sg._tolerances.ap_y
    set_mock_value(ap_sg._aperture.large, 0)
    set_mock_value(ap_sg._aperture.medium, 0)
    set_mock_value(ap_sg._aperture.small, 0)
    await ap_sg._aperture.y.set(robot_load_ap_y + tolerance)
    assert await ap_sg.get_current_aperture_position() == robot_load


async def test_aperture_positions_robot_load_outside_tolerance(
    ap_sg: ApertureScatterguard,
    aperture_positions: dict[AperturePosition, SingleAperturePosition],
):
    robot_load = aperture_positions[AperturePosition.ROBOT_LOAD]
    robot_load_ap_y = robot_load.location.aperture_y
    tolerance = ap_sg._tolerances.ap_y + 0.01
    set_mock_value(ap_sg._aperture.large, 0)
    set_mock_value(ap_sg._aperture.medium, 0)
    set_mock_value(ap_sg._aperture.small, 0)
    await ap_sg._aperture.y.set(robot_load_ap_y + tolerance)
    with pytest.raises(InvalidApertureMove):
        await ap_sg.get_current_aperture_position()


async def test_aperture_positions_robot_load_unsafe(
    ap_sg: ApertureScatterguard,
):
    set_mock_value(ap_sg._aperture.large, 0)
    set_mock_value(ap_sg._aperture.medium, 0)
    set_mock_value(ap_sg._aperture.small, 0)
    await ap_sg._aperture.y.set(50.0)
    with pytest.raises(InvalidApertureMove):
        await ap_sg.get_current_aperture_position()


async def test_given_aperture_not_set_through_device_but_motors_in_position_when_device_read_then_position_returned(
    aperture_in_medium_pos: ApertureScatterguard,
    aperture_positions: dict[AperturePosition, SingleAperturePosition],
):
    selected_aperture = await aperture_in_medium_pos.read()
    assert isinstance(selected_aperture, dict)
    assert selected_aperture["test_ap_sg-selected_aperture"]["value"] == asdict(
        aperture_positions[AperturePosition.MEDIUM]
    )


async def test_when_aperture_set_and_device_read_then_position_returned(
    aperture_in_medium_pos: ApertureScatterguard,
    aperture_positions: dict[AperturePosition, SingleAperturePosition],
):
    await aperture_in_medium_pos.set((ApertureInOut.IN, AperturePosition.MEDIUM))
    selected_aperture = await aperture_in_medium_pos.read()
    assert selected_aperture["test_ap_sg-selected_aperture"]["value"] == asdict(
        aperture_positions[AperturePosition.MEDIUM]
    )


async def test_ap_sg_in_runengine(
    aperture_in_medium_pos: ApertureScatterguard,
    RE: RunEngine,
    aperture_positions: dict[AperturePosition, SingleAperturePosition],
):
    ap_sg = aperture_in_medium_pos
    ap = ap_sg._aperture
    sg = ap_sg._scatterguard
    test_loc = aperture_positions[AperturePosition.SMALL].location
    RE(bps.abs_set(ap_sg, (ApertureInOut.IN, AperturePosition.SMALL), wait=True))
    assert await ap.x.user_readback.get_value() == test_loc.aperture_x
    assert await ap.y.user_readback.get_value() == test_loc.aperture_y
    assert await ap.z.user_readback.get_value() == test_loc.aperture_z
    assert await sg.x.user_readback.get_value() == test_loc.scatterguard_x
    assert await sg.y.user_readback.get_value() == test_loc.scatterguard_y


async def test_ap_sg_descriptor(
    aperture_in_medium_pos: ApertureScatterguard,
):
    description = await aperture_in_medium_pos.describe()
    assert description


def test_get_position_from_gda_aperture_name(
    ap_sg: ApertureScatterguard,
):
    assert (
        ap_sg.get_position_from_gda_aperture_name(
            AperturePositionGDANames.LARGE_APERTURE
        )
        == AperturePosition.LARGE
    )
    assert (
        ap_sg.get_position_from_gda_aperture_name(
            AperturePositionGDANames.MEDIUM_APERTURE
        )
        == AperturePosition.MEDIUM
    )
    assert (
        ap_sg.get_position_from_gda_aperture_name(
            AperturePositionGDANames.SMALL_APERTURE
        )
        == AperturePosition.SMALL
    )
    assert (
        ap_sg.get_position_from_gda_aperture_name(AperturePositionGDANames.ROBOT_LOAD)
        == AperturePosition.ROBOT_LOAD
    )
    with pytest.raises(ValueError):
        ap_sg.get_position_from_gda_aperture_name(
            "VERY TINY APERTURE"  # type: ignore
        )


def test_ap_sg_returns_GDA_name_correctly(ap_sg: ApertureScatterguard):
    assert ap_sg.get_gda_name_for_position(AperturePosition.SMALL) == "SMALL_APERTURE"


async def test_when_move_out_and_none_then_mini_apt_y_moves_to_robot_load_position_and_no_other_axes_move(
    ap_sg: ApertureScatterguard,
):
    await ap_sg.set((ApertureInOut.OUT, None))
    get_mock_put(ap_sg._aperture.y.user_setpoint).assert_called_once_with(
        31.40, wait=ANY, timeout=ANY
    )
    get_mock_put(ap_sg._aperture.x.user_setpoint).assert_not_called()
    get_mock_put(ap_sg._aperture.z.user_setpoint).assert_not_called()
    get_mock_put(ap_sg._scatterguard.x.user_setpoint).assert_not_called()
    get_mock_put(ap_sg._scatterguard.y.user_setpoint).assert_not_called()


@pytest.mark.parametrize(
    "position",
    [
        AperturePosition.SMALL,
        AperturePosition.MEDIUM,
        AperturePosition.LARGE,
    ],
)
async def test_when_move_out_and_a_position_then_mini_apt_y_moves_to_robot_load_y_and_other_axes_move_to_aperture_position(
    ap_sg: ApertureScatterguard, position: AperturePosition
):
    location = ap_sg._loaded_positions[position].location

    await ap_sg.set((ApertureInOut.OUT, position))
    assert await ap_sg._aperture.y.user_readback.get_value() == 31.40
    assert await ap_sg._aperture.x.user_readback.get_value() == location.aperture_x
    assert await ap_sg._aperture.z.user_readback.get_value() == location.aperture_z
    assert (
        await ap_sg._scatterguard.x.user_readback.get_value() == location.scatterguard_x
    )
    assert (
        await ap_sg._scatterguard.y.user_readback.get_value() == location.scatterguard_y
    )


async def test_when_move_in_and_no_aperture_then_raise_exception(
    ap_sg: ApertureScatterguard,
):
    with pytest.raises(InvalidApertureMove):
        await ap_sg.set((ApertureInOut.IN, None))
