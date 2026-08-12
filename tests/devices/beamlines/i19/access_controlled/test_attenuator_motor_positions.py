import math
from typing import Any, Final

import pytest
from pydantic import ValidationError

from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorPositions,
)

TRIAL_AXIAL_MOTOR_POSITIONS: Final[list[float]] = [
    -4.3,
    -2,
    0.01,
    0.0,
    12.6,
    38,
    90.104,
]


@pytest.mark.parametrize(
    "motor_name",
    [
        "_x",
        "Y",
        "_h",
        "_Vert",
        "V4",
        "x",
        "y",
    ],
)
@pytest.mark.parametrize(
    "trial_motor_position_mm",
    TRIAL_AXIAL_MOTOR_POSITIONS,
)
def test_that_attenuator_motor_positions_can_be_created_for_just_the_one_wedge(
    motor_name: str, trial_motor_position_mm: float
) -> None:
    wedge_position_demands = {motor_name: trial_motor_position_mm}
    wheel_position_demands = {}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_position_demands,
        discrete_indices=wheel_position_demands,
    )
    assert position_demand is not None


@pytest.mark.parametrize(
    "trial_motor_position_mm",
    TRIAL_AXIAL_MOTOR_POSITIONS,
)
def test_that_attenuator_motor_positions_with_for_one_wedge_provides_expected_rest_format(
    trial_motor_position_mm: float,
) -> None:
    wedge_position_demands = {"y": trial_motor_position_mm}
    wheel_position_demands = {}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_position_demands,
        discrete_indices=wheel_position_demands,
    )
    restful_payload = position_demand.validated_and_complete()
    assert restful_payload["y"] == trial_motor_position_mm


TRIAL_WHEEL_INDICES = [
    1,
    2,
    4,
    5,
    3,
    6,
    8,
]

WHEEL_NAMES = ["w", "V", "_w1", "_W_one", "w4", "spare_wheel"]

# split testing matrix across two tests to reduce the number of cases without losing
# variety / stress testing


@pytest.mark.parametrize("wheel_name", ["u", "t"])
@pytest.mark.parametrize(
    "trial_index",
    TRIAL_WHEEL_INDICES,
)
def test_that_attenuator_motor_positions_can_be_created_for_only_one_wheel_at_any_index(
    wheel_name: str, trial_index: int
) -> None:
    wedge_position_demands = {}
    wheel_position_demands = {wheel_name: trial_index}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_position_demands,
        discrete_indices=wheel_position_demands,
    )
    assert position_demand is not None


@pytest.mark.parametrize(
    "wheel_name",
    WHEEL_NAMES,
)
@pytest.mark.parametrize(
    "trial_index",
    [3, 4],
)
def test_that_attenuator_motor_positions_for_only_one_wheel_can_be_created_with_any_wheel_name(
    wheel_name: str, trial_index: int
) -> None:
    wedge_position_demands = {}
    wheel_position_demands = {wheel_name: trial_index}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_position_demands,
        discrete_indices=wheel_position_demands,
    )
    assert position_demand is not None


@pytest.mark.parametrize(
    "trial_index",
    TRIAL_WHEEL_INDICES,
)
def test_that_attenuator_motor_positions_for_only_one_wheel_provides_expected_rest_format(
    trial_index: int,
) -> None:
    wedge_position_demands = {}
    wheel_position_demands = {"w": trial_index}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_position_demands,
        discrete_indices=wheel_position_demands,
    )
    restful_payload = position_demand.validated_and_complete()
    assert restful_payload["w"] == trial_index


def test_that_empty_attenuator_motor_positions_can_be_created() -> None:
    wedge_position_demands = {}
    wheel_position_demands = {}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_position_demands,
        discrete_indices=wheel_position_demands,
    )
    assert position_demand is not None


def test_that_empty_attenuator_motor_positions_provides_empty_rest_format() -> None:
    wedge_position_demands = {}
    wheel_position_demands = {}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_position_demands,
        discrete_indices=wheel_position_demands,
    )
    restful_payload = position_demand.validated_and_complete()
    expected_rest_dict = {}
    assert restful_payload == expected_rest_dict


@pytest.mark.parametrize(
    "trial_motor_position_mm",
    TRIAL_AXIAL_MOTOR_POSITIONS,
)
@pytest.mark.parametrize(
    "trial_index",
    TRIAL_WHEEL_INDICES,
)
def test_that_attenuator_motor_positions_triplet_can_be_created(
    trial_motor_position_mm: float, trial_index: int
) -> None:
    standard_wedge_position_demand = {"x": trial_motor_position_mm, "y": 5.0}
    standard_wheel_position_demand = {"w": trial_index}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=standard_wedge_position_demand,
        discrete_indices=standard_wheel_position_demand,
    )
    assert position_demand is not None


def test_that_attenuator_motor_positions_triplet_provides_expected_rest_format() -> (
    None
):
    wedge_position_demands = {"x": 0.1, "y": 90.1}
    wheel_position_demands = {"w": 6}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_position_demands,
        discrete_indices=wheel_position_demands,
    )
    restful_payload = position_demand.validated_and_complete()
    expected_rest_dict = {"x": 0.1, "y": 90.1, "w": 6}
    assert restful_payload == expected_rest_dict


@pytest.mark.parametrize(
    "trial_index",
    TRIAL_WHEEL_INDICES,
)
def test_that_attenuator_motor_keys_accepts_leading_underscores_or_upper_case_letters(
    trial_index: int,
) -> None:
    wedge_position_demands = {"_x": 0.1, "Y": 90.1}
    wheel_position_demands = {"_W": trial_index}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_position_demands,
        discrete_indices=wheel_position_demands,
    )
    restful_payload = position_demand.validated_and_complete()
    expected_rest_dict = {"_x": 0.1, "Y": 90.1, "_W": trial_index}
    assert restful_payload == expected_rest_dict


# Happy path tests above

# Unhappy path tests below


def test_that_attenuator_motor_positions_raises_error_when_discrete_and_continuous_demands_overload_axis_label() -> (
    None
):
    wedge_position_demands = {"x": 0.1, "v": 90.1}
    wheel_position_demands = {"w": 6, "v": 7}
    anticipated_preamble: str = (
        f"1 validation error for {AttenuatorMotorPositions.__name__}"
    )
    with pytest.raises(expected_exception=ValueError, match=anticipated_preamble):
        AttenuatorMotorPositions(
            continuous_positions=wedge_position_demands,
            discrete_indices=wheel_position_demands,
        )


INVALID_FLOATS: Final = [
    None,
    ValueError(),
    "8.0",  # ie String rather than numerical float is invalid
    "14",
    "k",
    "",
    "game_over",
    math.cos,
    object(),
    False,
    True,
]


@pytest.mark.parametrize(
    "invalid_x",
    INVALID_FLOATS,
)
def test_that_attenuator_motor_positions_creation_raises_error_when_continuous_position_is_invalid(
    invalid_x,
) -> None:
    wedge_position_demands = {"x": invalid_x, "y": 90.1}
    wheel_position_demands = {}
    with pytest.raises(expected_exception=ValidationError):
        AttenuatorMotorPositions(
            continuous_positions=wedge_position_demands,
            discrete_indices=wheel_position_demands,
        )


# indices need to be positive non-zero naturals
INVALID_NATURALS: Final[list[Any]] = [
    None,
    -3,
    0,
    "2.0",
    "-12",
    "5",
    "q",
    "",
    "longer_string",
    math.exp,
    AttributeError(),
    object(),
    False,
    True,
]


@pytest.mark.parametrize(
    "invalid_w",
    INVALID_NATURALS,
)
def test_that_attenuator_motor_positions_creation_raises_error_when_indexed_position_is_invalid(
    invalid_w,
) -> None:
    wedge_position_demands = {"x": 14.88, "y": 90.1}
    wheel_position_demands = {"w": invalid_w, "v": 3}
    with pytest.raises(expected_exception=ValidationError):
        AttenuatorMotorPositions(
            continuous_positions=wedge_position_demands,
            discrete_indices=wheel_position_demands,
        )


INVALID_MOTOR_IDENTIFIERS: Final[list[Any]] = [
    None,
    6,
    -98.7,
    "-9.87",
    "",
    " ",
    ".a1",
    "$7",
    "2B",
    "-U",
    "x6^",
    0,
    math.cos,
    AttributeError(),
    object(),
    False,
    True,
]


@pytest.mark.parametrize(
    "invalid_key",
    INVALID_MOTOR_IDENTIFIERS,
)
def test_that_attenuator_motor_positions_creation_raises_error_when_continuous_position_key_is_invalid(
    invalid_key,
) -> None:
    wedge_position_demands = {"x": 32.65, invalid_key: 80.1}
    wheel_position_demands = {"w": 8}
    with pytest.raises(expected_exception=ValidationError):
        AttenuatorMotorPositions(
            continuous_positions=wedge_position_demands,
            discrete_indices=wheel_position_demands,
        )


@pytest.mark.parametrize(
    "invalid_key",
    INVALID_MOTOR_IDENTIFIERS,
)
def test_that_attenuator_motor_positions_creation_raises_error_when_indexed_position_key_is_invalid(
    invalid_key,
) -> None:
    wedge_position_demands = {"x": 24.08, "y": 71.4}
    wheel_position_demands = {"w": 1, invalid_key: 2}
    with pytest.raises(expected_exception=ValidationError):
        AttenuatorMotorPositions(
            continuous_positions=wedge_position_demands,
            discrete_indices=wheel_position_demands,
        )
