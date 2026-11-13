import ast
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
    wedge_positions = {motor_name: trial_motor_position_mm}
    wheel_positions = {}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_positions,
        discrete_indices=wheel_positions,
    )
    assert position_demand is not None


@pytest.mark.parametrize(
    "trial_motor_position_mm",
    TRIAL_AXIAL_MOTOR_POSITIONS,
)
def test_that_attenuator_motor_positions_for_one_wedge_provides_expected_rest_format(
    trial_motor_position_mm: float,
) -> None:
    wedge_positions = {"y": trial_motor_position_mm}
    wheel_positions = {}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_positions,
        discrete_indices=wheel_positions,
    )
    restful_payload = position_demand.validated_and_complete
    assert restful_payload["y"] == trial_motor_position_mm


@pytest.mark.parametrize(
    "trial_motor_position_mm",
    TRIAL_AXIAL_MOTOR_POSITIONS,
)
def test_that_attenuator_motor_positions_for_one_wedge_can_be_created_without_mentioning_wheel_positions(
    trial_motor_position_mm: float,
) -> None:
    wedge_positions = {"x": trial_motor_position_mm}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_positions,
    )
    restful_payload = position_demand.validated_and_complete
    assert restful_payload["x"] == trial_motor_position_mm


@pytest.mark.parametrize(
    "wedge_positions, wheel_indexes, expected_equivalent_dict",
    [
        ({"y": 93.3}, {}, {"y": 93.3}),
        ({}, {"v": 5}, {"v": 5}),
        ({"y": 15.2, "x": -1.05}, {"w": 1}, {"w": 1, "x": -1.05, "y": 15.2}),
        ({"x": 19.81}, {"w": 3}, {"w": 3, "x": 19.81}),
        ({"y": 25.6}, {"v": 4, "w": 3}, {"v": 4, "w": 3, "y": 25.6}),
        ({"x": 13.04, "y": 26.5}, {}, {"x": 13.04, "y": 26.5}),
    ],
)
def test_that_attenuator_motor_positions_repr_to_the_expected_string(
    wedge_positions: dict[str, float],
    wheel_indexes: dict[str, int],
    expected_equivalent_dict: dict[str, float | int],
) -> None:

    amp = AttenuatorMotorPositions(
        continuous_positions=wedge_positions, discrete_indices=wheel_indexes
    )
    equivalent_dict = ast.literal_eval(repr(amp))
    assert equivalent_dict == expected_equivalent_dict


@pytest.mark.parametrize(
    "wedge_positions1, wheel_indexes1, wedge_positions2, wheel_indexes2",
    [
        ({"x": 2.3}, {}, {"x": 2.3}, {}),
        ({"y": 93.3}, {"w": 4}, {"y": 93.3}, {"w": 4}),
        ({"x": 93.3, "y": 15.5}, {"w": 4}, {"y": 15.5, "x": 93.3}, {"w": 4}),
    ],
)
def test_that_equivalent_attenuator_motor_positions_are_equal(
    wedge_positions1: dict[str, float],
    wheel_indexes1: dict[str, int],
    wedge_positions2: dict[str, float],
    wheel_indexes2: dict[str, int],
) -> None:
    amp1 = AttenuatorMotorPositions(
        continuous_positions=wedge_positions1, discrete_indices=wheel_indexes1
    )
    amp2 = AttenuatorMotorPositions(
        continuous_positions=wedge_positions2, discrete_indices=wheel_indexes2
    )
    assert amp1 == amp2


@pytest.mark.parametrize(
    "wedge_positions1, wheel_indexes1, wedge_positions2, wheel_indexes2",
    [
        ({"y": 2.3}, {}, {"x": 2.3}, {}),
        ({"y": 12.3}, {"w": 2}, {"y": 12.3}, {}),
        ({"y": 93.3}, {"w": 3}, {"y": 93.3}, {"w": 4}),
        ({"y": 17.4}, {"w": 3}, {"y": 93.3}, {"w": 3}),
        ({"x": 18}, {}, {"y": 18}, {}),
        ({"x": 93.3, "y": 15.5}, {"w": 4}, {"y": 10.5, "x": 93.3}, {"w": 4}),
    ],
)
def test_that_distinct_attenuator_motor_positions_are_not_spuriously_considered_equal(
    wedge_positions1: dict[str, float],
    wheel_indexes1: dict[str, int],
    wedge_positions2: dict[str, float],
    wheel_indexes2: dict[str, int],
) -> None:
    amp1 = AttenuatorMotorPositions(
        continuous_positions=wedge_positions1, discrete_indices=wheel_indexes1
    )
    amp2 = AttenuatorMotorPositions(
        continuous_positions=wedge_positions2, discrete_indices=wheel_indexes2
    )
    assert amp1 != amp2


@pytest.mark.parametrize(
    "wedge_positions1, wheel_indexes1, wedge_positions2, wheel_indexes2, expected_merged_positions",
    [
        ({"y": 93.3}, {"w": 4}, {"x": 72.1}, {}, {"w": 4, "x": 72.1, "y": 93.3}),
        ({}, {"v": 5}, {}, {"w": 1}, {"v": 5, "w": 1}),
        ({"x": 50.01}, {}, {}, {"w": 1}, {"x": 50.01, "w": 1}),
        ({}, {"w": 3}, {"y": 30.29}, {}, {"y": 30.29, "w": 3}),
        ({}, {}, {"y": 45.06}, {}, {"y": 45.06}),
    ],
)
def test_that_attenuator_motor_positions_can_be_merged(
    wedge_positions1: dict[str, float],
    wheel_indexes1: dict[str, int],
    wedge_positions2: dict[str, float],
    wheel_indexes2: dict[str, int],
    expected_merged_positions: dict[str, float | int],
) -> None:
    amp1 = AttenuatorMotorPositions(
        continuous_positions=wedge_positions1, discrete_indices=wheel_indexes1
    )
    amp2 = AttenuatorMotorPositions(
        continuous_positions=wedge_positions2, discrete_indices=wheel_indexes2
    )
    merged_amp = amp1 | amp2
    equivalent_dict = ast.literal_eval(repr(merged_amp))
    assert equivalent_dict == expected_merged_positions


@pytest.mark.parametrize("thing", [object(), 5.5, "Hello", KeyError(), False, True, -9])
def test_that_attenuator_motor_positions_ignore_merge_with_other_types(
    thing: Any,
) -> None:
    amp = AttenuatorMotorPositions(
        continuous_positions={"x": 27.5, "y": 12.6}, discrete_indices={"w": 3}
    )
    amp2 = amp | thing
    assert amp2 is amp


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
    wedge_positions = {}
    wheel_positions = {wheel_name: trial_index}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_positions,
        discrete_indices=wheel_positions,
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
    wedge_positions = {}
    wheel_positions = {wheel_name: trial_index}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_positions,
        discrete_indices=wheel_positions,
    )
    assert position_demand is not None


@pytest.mark.parametrize(
    "trial_index",
    TRIAL_WHEEL_INDICES,
)
def test_that_attenuator_motor_positions_for_only_one_wheel_provides_expected_rest_format(
    trial_index: int,
) -> None:
    wedge_positions = {}
    wheel_positions = {"w": trial_index}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_positions,
        discrete_indices=wheel_positions,
    )
    restful_payload = position_demand.validated_and_complete
    assert restful_payload["w"] == trial_index


@pytest.mark.parametrize(
    "trial_index",
    TRIAL_WHEEL_INDICES,
)
def test_that_attenuator_motor_positions_for_only_one_wheel_can_be_created_without_mentioning_wedge_positions(
    trial_index: int,
) -> None:
    wheel_positions = {"w": trial_index}
    position_demand = AttenuatorMotorPositions(
        discrete_indices=wheel_positions,
    )
    restful_payload = position_demand.validated_and_complete
    assert restful_payload["w"] == trial_index


def test_that_empty_attenuator_motor_positions_can_be_created() -> None:
    wedge_positions = {}
    wheel_positions = {}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_positions,
        discrete_indices=wheel_positions,
    )
    assert position_demand is not None


def test_that_empty_attenuator_motor_positions_can_be_created_relying_on_default_args() -> (
    None
):
    position_demand = AttenuatorMotorPositions()
    assert position_demand is not None


def test_that_two_empty_attenuator_motor_positions_are_both_equal() -> None:
    position1 = AttenuatorMotorPositions()
    position2 = AttenuatorMotorPositions(continuous_positions={}, discrete_indices={})
    assert position1 == position2


def test_that_empty_attenuator_motor_positions_provides_empty_rest_format() -> None:
    wedge_positions = {}
    wheel_positions = {}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_positions,
        discrete_indices=wheel_positions,
    )
    restful_payload = position_demand.validated_and_complete
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
    wedge_positions = {"x": 0.1, "y": 90.1}
    wheel_positions = {"w": 6}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_positions,
        discrete_indices=wheel_positions,
    )
    restful_payload = position_demand.validated_and_complete
    expected_rest_dict = {"x": 0.1, "y": 90.1, "w": 6}
    assert restful_payload == expected_rest_dict


@pytest.mark.parametrize(
    "trial_index",
    TRIAL_WHEEL_INDICES,
)
def test_that_attenuator_motor_keys_accepts_leading_underscores_or_upper_case_letters(
    trial_index: int,
) -> None:
    wedge_positions = {"_x": 0.1, "Y": 90.1}
    wheel_positions = {"_W": trial_index}
    position_demand = AttenuatorMotorPositions(
        continuous_positions=wedge_positions,
        discrete_indices=wheel_positions,
    )
    restful_payload = position_demand.validated_and_complete
    expected_rest_dict = {"_x": 0.1, "Y": 90.1, "_W": trial_index}
    assert restful_payload == expected_rest_dict


# Happy path tests above

# Unhappy path tests below


def test_that_attenuator_motor_positions_raises_error_when_discrete_and_continuouss_overload_axis_label() -> (
    None
):
    wedge_positions = {"x": 0.1, "v": 90.1}
    wheel_positions = {"w": 6, "v": 7}
    anticipated_preamble: str = (
        f"1 validation error for {AttenuatorMotorPositions.__name__}"
    )
    with pytest.raises(expected_exception=ValueError, match=anticipated_preamble):
        AttenuatorMotorPositions(
            continuous_positions=wedge_positions,
            discrete_indices=wheel_positions,
        )


@pytest.mark.parametrize(
    "wedge_positions1, wheel_indexes1, wedge_positions2, wheel_indexes2",
    [
        ({"x": 93.3}, {"w": 4}, {"x": 72.1}, {}),
        ({}, {"w": 5}, {}, {"w": 1}),
        ({"x": 50.01}, {"w": 3}, {"y": 30.3}, {"w": 1}),
        ({"y": 10.1}, {"v": 2}, {"y": 68.4}, {"v": 2}),
    ],
)
def test_that_attenuator_motor_positions_cannot_be_merged_when_identities_clash(
    wedge_positions1: dict[str, float],
    wheel_indexes1: dict[str, int],
    wedge_positions2: dict[str, float],
    wheel_indexes2: dict[str, int],
) -> None:
    amp1 = AttenuatorMotorPositions(
        continuous_positions=wedge_positions1, discrete_indices=wheel_indexes1
    )
    amp2 = AttenuatorMotorPositions(
        continuous_positions=wedge_positions2, discrete_indices=wheel_indexes2
    )
    with pytest.raises(ValueError):
        _unmergeable = amp1 | amp2


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
    wedge_positions = {"x": invalid_x, "y": 90.1}
    wheel_positions = {}
    with pytest.raises(expected_exception=ValidationError):
        AttenuatorMotorPositions(
            continuous_positions=wedge_positions,
            discrete_indices=wheel_positions,
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
    wedge_positions = {"x": 14.88, "y": 90.1}
    wheel_positions = {"w": invalid_w, "v": 3}
    with pytest.raises(expected_exception=ValidationError):
        AttenuatorMotorPositions(
            continuous_positions=wedge_positions,
            discrete_indices=wheel_positions,
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
    wedge_positions = {"x": 32.65, invalid_key: 80.1}
    wheel_positions = {"w": 8}
    with pytest.raises(expected_exception=ValidationError):
        AttenuatorMotorPositions(
            continuous_positions=wedge_positions,
            discrete_indices=wheel_positions,
        )


@pytest.mark.parametrize(
    "invalid_key",
    INVALID_MOTOR_IDENTIFIERS,
)
def test_that_attenuator_motor_positions_creation_raises_error_when_indexed_position_key_is_invalid(
    invalid_key,
) -> None:
    wedge_positions = {"x": 24.08, "y": 71.4}
    wheel_positions = {"w": 1, invalid_key: 2}
    with pytest.raises(expected_exception=ValidationError):
        AttenuatorMotorPositions(
            continuous_positions=wedge_positions,
            discrete_indices=wheel_positions,
        )
