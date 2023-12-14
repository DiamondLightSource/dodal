from unittest.mock import MagicMock

import pytest
from ophyd.sim import make_fake_device
from ophyd.status import Status, StatusBase

from dodal.devices.aperturescatterguard import (
    AperturePositions,
    ApertureScatterguard,
    InvalidApertureMove,
)


@pytest.fixture
def fake_aperture_scatterguard():
    FakeApertureScatterguard = make_fake_device(ApertureScatterguard)
    ap_sg: ApertureScatterguard = FakeApertureScatterguard(name="test_ap_sg")
    yield ap_sg


@pytest.fixture
def aperture_in_medium_pos(
    fake_aperture_scatterguard: ApertureScatterguard,
    aperture_positions: AperturePositions,
):
    fake_aperture_scatterguard.load_aperture_positions(aperture_positions)
    fake_aperture_scatterguard.aperture.x.user_setpoint.sim_put(  # type: ignore
        aperture_positions.MEDIUM[0]
    )
    fake_aperture_scatterguard.aperture.y.user_setpoint.sim_put(  # type: ignore
        aperture_positions.MEDIUM[1]
    )
    fake_aperture_scatterguard.aperture.z.user_setpoint.sim_put(  # type: ignore
        aperture_positions.MEDIUM[2]
    )
    fake_aperture_scatterguard.aperture.x.user_readback.sim_put(  # type: ignore
        aperture_positions.MEDIUM[1]
    )
    fake_aperture_scatterguard.aperture.y.user_readback.sim_put(  # type: ignore
        aperture_positions.MEDIUM[1]
    )
    fake_aperture_scatterguard.aperture.z.user_readback.sim_put(  # type: ignore
        aperture_positions.MEDIUM[1]
    )
    fake_aperture_scatterguard.scatterguard.x.user_setpoint.sim_put(  # type: ignore
        aperture_positions.MEDIUM[3]
    )
    fake_aperture_scatterguard.scatterguard.y.user_setpoint.sim_put(  # type: ignore
        aperture_positions.MEDIUM[4]
    )
    fake_aperture_scatterguard.scatterguard.x.user_readback.sim_put(  # type: ignore
        aperture_positions.MEDIUM[3]
    )
    fake_aperture_scatterguard.scatterguard.y.user_readback.sim_put(  # type: ignore
        aperture_positions.MEDIUM[4]
    )
    fake_aperture_scatterguard.aperture.x.motor_done_move.sim_put(1)  # type: ignore
    fake_aperture_scatterguard.aperture.y.motor_done_move.sim_put(1)  # type: ignore
    fake_aperture_scatterguard.aperture.z.motor_done_move.sim_put(1)  # type: ignore
    fake_aperture_scatterguard.scatterguard.x.motor_done_move.sim_put(1)  # type: ignore
    fake_aperture_scatterguard.scatterguard.y.motor_done_move.sim_put(1)  # type: ignore
    return fake_aperture_scatterguard


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


def test_aperture_scatterguard_rejects_unknown_position(
    aperture_positions, aperture_in_medium_pos
):
    for i in range(0, len(aperture_positions.MEDIUM)):
        position_to_reject = list(aperture_positions.MEDIUM)
        position_to_reject[i] += 0.01
        position_to_reject = tuple(position_to_reject)

        with pytest.raises(InvalidApertureMove):
            aperture_in_medium_pos.set(position_to_reject)


def test_aperture_scatterguard_select_bottom_moves_sg_down_then_assembly_up(
    aperture_positions, aperture_in_medium_pos
):
    aperture_scatterguard = aperture_in_medium_pos
    call_logger = install_logger_for_aperture_and_scatterguard(aperture_scatterguard)

    aperture_scatterguard.set(aperture_positions.SMALL)

    actual_calls = call_logger.mock_calls
    expected_calls = [
        ("_mock_sg_x", (5.3375,)),
        ("_mock_sg_y", (-3.55,)),
        lambda call: call[0].endswith("__and__().wait"),
        ("_mock_ap_x", (2.43,)),
        ("_mock_ap_y", (48.974,)),
        ("_mock_ap_z", (15.8,)),
    ]

    compare_actual_and_expected_calls(actual_calls, expected_calls)


def test_aperture_scatterguard_select_top_moves_assembly_down_then_sg_up(
    aperture_positions, aperture_in_medium_pos
):
    aperture_scatterguard = aperture_in_medium_pos
    call_logger = install_logger_for_aperture_and_scatterguard(aperture_scatterguard)

    aperture_scatterguard.set(aperture_positions.LARGE)

    actual_calls = call_logger.mock_calls
    expected_calls = [
        ("_mock_ap_x", (2.389,)),
        ("_mock_ap_y", (40.986,)),
        ("_mock_ap_z", (15.8,)),
        lambda call: call[0].endswith("__and__().wait"),
        ("_mock_sg_x", (5.25,)),
        ("_mock_sg_y", (4.43,)),
    ]

    compare_actual_and_expected_calls(actual_calls, expected_calls)


def test_aperture_scatterguard_throws_error_if_outside_tolerance(
    fake_aperture_scatterguard: ApertureScatterguard,
):
    fake_aperture_scatterguard.aperture.z.motor_resolution.sim_put(0.001)  # type: ignore
    fake_aperture_scatterguard.aperture.z.user_setpoint.sim_put(1)  # type: ignore
    fake_aperture_scatterguard.aperture.z.motor_done_move.sim_put(1)  # type: ignore

    with pytest.raises(InvalidApertureMove):
        fake_aperture_scatterguard._safe_move_within_datacollection_range(
            0, 0, 1.1, 0, 0
        )


def test_aperture_scatterguard_returns_status_if_within_tolerance(
    fake_aperture_scatterguard: ApertureScatterguard,
):
    fake_aperture_scatterguard.aperture.z.motor_resolution.sim_put(0.001)  # type: ignore
    fake_aperture_scatterguard.aperture.z.user_setpoint.sim_put(1)  # type: ignore
    fake_aperture_scatterguard.aperture.z.motor_done_move.sim_put(1)  # type: ignore

    mock_set = MagicMock(return_value=Status(done=True, success=True))

    fake_aperture_scatterguard.aperture.x.set = mock_set
    fake_aperture_scatterguard.aperture.y.set = mock_set
    fake_aperture_scatterguard.aperture.z.set = mock_set

    fake_aperture_scatterguard.scatterguard.x.set = mock_set
    fake_aperture_scatterguard.scatterguard.y.set = mock_set

    status = fake_aperture_scatterguard._safe_move_within_datacollection_range(
        0, 0, 1, 0, 0
    )
    assert isinstance(status, StatusBase)


def install_logger_for_aperture_and_scatterguard(aperture_scatterguard):
    parent_mock = MagicMock()
    mock_ap_x = MagicMock(aperture_scatterguard.aperture.x.set)
    mock_ap_y = MagicMock(aperture_scatterguard.aperture.y.set)
    mock_ap_z = MagicMock(aperture_scatterguard.aperture.z.set)
    mock_sg_x = MagicMock(aperture_scatterguard.scatterguard.x.set)
    mock_sg_y = MagicMock(aperture_scatterguard.scatterguard.y.set)
    aperture_scatterguard.aperture.x.set = mock_ap_x
    aperture_scatterguard.aperture.y.set = mock_ap_y
    aperture_scatterguard.aperture.z.set = mock_ap_z
    aperture_scatterguard.scatterguard.x.set = mock_sg_x
    aperture_scatterguard.scatterguard.y.set = mock_sg_y
    parent_mock.attach_mock(mock_ap_x, "_mock_ap_x")
    parent_mock.attach_mock(mock_ap_y, "_mock_ap_y")
    parent_mock.attach_mock(mock_ap_z, "_mock_ap_z")
    parent_mock.attach_mock(mock_sg_x, "_mock_sg_x")
    parent_mock.attach_mock(mock_sg_y, "_mock_sg_y")
    return parent_mock


def compare_actual_and_expected_calls(actual_calls, expected_calls):
    # ideally, we could use MagicMock.assert_has_calls but a) it doesn't work properly and b) doesn't do what I need
    i_actual = 0
    for i_expected in range(0, len(expected_calls)):
        try:
            expected = expected_calls[i_expected]
            if isinstance(expected, tuple):
                # simple comparison
                i_actual = actual_calls.index(expected_calls[i_expected], i_actual)
            else:
                # expected is a predicate to be satisfied
                i_matches = [
                    i
                    for i in range(i_actual, len(actual_calls))
                    if expected(actual_calls[i])
                ]
                if i_matches:
                    i_actual = i_matches[0]
                else:
                    raise ValueError("Couldn't find call matching predicate")
        except ValueError:
            assert (
                False
            ), f"Couldn't find call #{i_expected}: {expected_calls[i_expected]}"

        i_actual += 1
