from unittest.mock import MagicMock, call

import pytest
from ophyd.sim import make_fake_device
from ophyd.status import StatusBase

from dodal.devices.aperturescatterguard import (
    ApertureFiveDimensionalLocation,
    AperturePositions,
    ApertureScatterguard,
    InvalidApertureMove,
    SingleAperturePosition,
)

from .conftest import patch_motor


@pytest.fixture
def ap_sg(aperture_positions: AperturePositions):
    FakeApertureScatterguard = make_fake_device(ApertureScatterguard)
    ap_sg: ApertureScatterguard = FakeApertureScatterguard(name="test_ap_sg")
    ap_sg.load_aperture_positions(aperture_positions)
    with (
        patch_motor(ap_sg.aperture.x),
        patch_motor(ap_sg.aperture.y),
        patch_motor(ap_sg.aperture.z),
        patch_motor(ap_sg.scatterguard.x),
        patch_motor(ap_sg.scatterguard.y),
    ):
        yield ap_sg


@pytest.fixture
def aperture_in_medium_pos(
    ap_sg: ApertureScatterguard,
    aperture_positions: AperturePositions,
):
    medium = aperture_positions.MEDIUM.location
    ap_sg.aperture.x.set(medium.aperture_x)
    ap_sg.aperture.y.set(medium.aperture_y)
    ap_sg.aperture.z.set(medium.aperture_z)
    ap_sg.scatterguard.x.set(medium.scatterguard_x)
    ap_sg.scatterguard.y.set(medium.scatterguard_y)
    ap_sg.aperture.medium.sim_put(1)  # type: ignore
    yield ap_sg


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
        }
    )
    return aperture_positions


def test_aperture_scatterguard_rejects_unknown_position(aperture_in_medium_pos):
    position_to_reject = ApertureFiveDimensionalLocation(0, 0, 0, 0, 0)

    with pytest.raises(InvalidApertureMove):
        aperture_in_medium_pos.set(
            SingleAperturePosition("test", "GDA_NAME", 10, position_to_reject)
        )


def test_aperture_scatterguard_select_bottom_moves_sg_down_then_assembly_up(
    aperture_positions: AperturePositions,
    aperture_in_medium_pos: ApertureScatterguard,
):
    aperture_scatterguard = aperture_in_medium_pos
    call_logger = install_logger_for_aperture_and_scatterguard(aperture_scatterguard)

    aperture_scatterguard.set(aperture_positions.SMALL)

    call_logger.assert_has_calls(
        [
            call._mock_sg_x(5.3375),
            call._mock_sg_y(-3.55),
            call._mock_ap_x(2.43),
            call._mock_ap_y(48.974),
            call._mock_ap_z(15.8),
        ]
    )


def test_aperture_unsafe_move(
    aperture_positions: AperturePositions,
    aperture_in_medium_pos: ApertureScatterguard,
):
    (a, b, c, d, e) = (0.2, 3.4, 5.6, 7.8, 9.0)
    aperture_scatterguard = aperture_in_medium_pos
    call_logger = install_logger_for_aperture_and_scatterguard(aperture_scatterguard)
    aperture_scatterguard._set_raw_unsafe((a, b, c, d, e))  # type: ignore

    call_logger.assert_has_calls(
        [
            call._mock_ap_x(a),
            call._mock_ap_y(b),
            call._mock_ap_z(c),
            call._mock_sg_x(d),
            call._mock_sg_y(e),
        ]
    )


def test_aperture_scatterguard_select_top_moves_assembly_down_then_sg_up(
    aperture_positions: AperturePositions, aperture_in_medium_pos: ApertureScatterguard
):
    aperture_scatterguard = aperture_in_medium_pos
    call_logger = install_logger_for_aperture_and_scatterguard(aperture_scatterguard)

    aperture_scatterguard.set(aperture_positions.LARGE)

    call_logger.assert_has_calls(
        [
            call._mock_ap_x(2.389),
            call._mock_ap_y(40.986),
            call._mock_ap_z(15.8),
            call._mock_sg_x(5.25),
            call._mock_sg_y(4.43),
        ]
    )


def test_aperture_scatterguard_throws_error_if_outside_tolerance(
    ap_sg: ApertureScatterguard,
):
    ap_sg.aperture.z.motor_resolution.sim_put(0.001)  # type: ignore
    ap_sg.aperture.z.user_setpoint.sim_put(1)  # type: ignore
    ap_sg.aperture.z.motor_done_move.sim_put(1)  # type: ignore

    with pytest.raises(InvalidApertureMove):
        pos = ApertureFiveDimensionalLocation(0, 0, 1.1, 0, 0)
        ap_sg._safe_move_within_datacollection_range(pos)


def test_aperture_scatterguard_returns_status_if_within_tolerance(
    ap_sg: ApertureScatterguard,
):
    ap_sg.aperture.z.motor_resolution.sim_put(0.001)  # type: ignore
    ap_sg.aperture.z.user_setpoint.sim_put(1)  # type: ignore
    ap_sg.aperture.z.motor_done_move.sim_put(1)  # type: ignore

    pos = ApertureFiveDimensionalLocation(0, 0, 1, 0, 0)
    status = ap_sg._safe_move_within_datacollection_range(pos)
    assert isinstance(status, StatusBase)


def set_underlying_motors(
    ap_sg: ApertureScatterguard, position: ApertureFiveDimensionalLocation
):
    ap_sg.aperture.x.set(position.aperture_x)
    ap_sg.aperture.y.set(position.aperture_y)
    ap_sg.aperture.z.set(position.aperture_z)
    ap_sg.scatterguard.x.set(position.scatterguard_x)
    ap_sg.scatterguard.y.set(position.scatterguard_y)


def test_aperture_positions_large(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    ap_sg.aperture.large.sim_put(1)  # type: ignore
    assert ap_sg._get_current_aperture_position() == aperture_positions.LARGE


def test_aperture_positions_medium(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    ap_sg.aperture.medium.sim_put(1)  # type: ignore
    assert ap_sg._get_current_aperture_position() == aperture_positions.MEDIUM


def test_aperture_positions_small(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    ap_sg.aperture.small.sim_put(1)  # type: ignore
    assert ap_sg._get_current_aperture_position() == aperture_positions.SMALL


def test_aperture_positions_robot_load(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    ap_sg.aperture.large.sim_put(0)  # type: ignore
    ap_sg.aperture.medium.sim_put(0)  # type: ignore
    ap_sg.aperture.small.sim_put(0)  # type: ignore
    ap_sg.aperture.y.set(aperture_positions.ROBOT_LOAD.location.aperture_y)  # type: ignore
    assert ap_sg._get_current_aperture_position() == aperture_positions.ROBOT_LOAD


def test_aperture_positions_robot_load_within_tolerance(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    robot_load_ap_y = aperture_positions.ROBOT_LOAD.location.aperture_y
    tolerance = ap_sg.TOLERANCE_STEPS * ap_sg.aperture.y.motor_resolution.get()
    ap_sg.aperture.large.sim_put(0)  # type: ignore
    ap_sg.aperture.medium.sim_put(0)  # type: ignore
    ap_sg.aperture.small.sim_put(0)  # type: ignore
    ap_sg.aperture.y.set(robot_load_ap_y + tolerance)  # type: ignore
    assert ap_sg._get_current_aperture_position() == aperture_positions.ROBOT_LOAD


def test_aperture_positions_robot_load_outside_tolerance(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    robot_load_ap_y = aperture_positions.ROBOT_LOAD.location.aperture_y
    tolerance = (ap_sg.TOLERANCE_STEPS + 1) * ap_sg.aperture.y.motor_resolution.get()
    ap_sg.aperture.large.sim_put(0)  # type: ignore
    ap_sg.aperture.medium.sim_put(0)  # type: ignore
    ap_sg.aperture.small.sim_put(0)  # type: ignore
    ap_sg.aperture.y.set(robot_load_ap_y + tolerance)  # type: ignore
    with pytest.raises(InvalidApertureMove):
        ap_sg._get_current_aperture_position()


def test_aperture_positions_robot_load_unsafe(
    ap_sg: ApertureScatterguard, aperture_positions: AperturePositions
):
    ap_sg.aperture.large.sim_put(0)  # type: ignore
    ap_sg.aperture.medium.sim_put(0)  # type: ignore
    ap_sg.aperture.small.sim_put(0)  # type: ignore
    ap_sg.aperture.y.set(50.0)  # type: ignore
    with pytest.raises(InvalidApertureMove):
        ap_sg._get_current_aperture_position()


def test_given_aperture_not_set_through_device_but_motors_in_position_when_device_read_then_position_returned(
    aperture_in_medium_pos: ApertureScatterguard, aperture_positions: AperturePositions
):
    selected_aperture = aperture_in_medium_pos.read()
    assert (
        selected_aperture["test_ap_sg_selected_aperture"]["value"]
        == aperture_positions.MEDIUM
    )


def test_when_aperture_set_and_device_read_then_position_returned(
    aperture_in_medium_pos: ApertureScatterguard, aperture_positions: AperturePositions
):
    set_status = aperture_in_medium_pos.set(aperture_positions.MEDIUM)
    set_status.wait()
    selected_aperture = aperture_in_medium_pos.read()
    assert (
        selected_aperture["test_ap_sg_selected_aperture"]["value"]
        == aperture_positions.MEDIUM
    )


def install_logger_for_aperture_and_scatterguard(aperture_scatterguard):
    parent_mock = MagicMock()
    mock_ap_x = aperture_scatterguard.aperture.x.set
    mock_ap_y = aperture_scatterguard.aperture.y.set
    mock_ap_z = aperture_scatterguard.aperture.z.set
    mock_sg_x = aperture_scatterguard.scatterguard.x.set
    mock_sg_y = aperture_scatterguard.scatterguard.y.set
    parent_mock.attach_mock(mock_ap_x, "_mock_ap_x")
    parent_mock.attach_mock(mock_ap_y, "_mock_ap_y")
    parent_mock.attach_mock(mock_ap_z, "_mock_ap_z")
    parent_mock.attach_mock(mock_sg_x, "_mock_sg_x")
    parent_mock.attach_mock(mock_sg_y, "_mock_sg_y")
    return parent_mock
