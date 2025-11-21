import pytest

from dodal.devices.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorPositionDemands,
)


def test_that_attenuator_position_demand_can_be_created_with_only_one_wedge():
    wedge_position_demands = {"x": 0.5}
    wheel_position_demands = {}
    position_demand = AttenuatorMotorPositionDemands(
        continuous_demands=wedge_position_demands,
        indexed_demands=wheel_position_demands,
    )
    assert position_demand is not None


def test_that_attenuator_position_demand_with_only_one_wedge_provides_expected_rest_format():
    wedge_position_demands = {"y": 14.9}
    wheel_position_demands = {}
    position_demand = AttenuatorMotorPositionDemands(
        continuous_demands=wedge_position_demands,
        indexed_demands=wheel_position_demands,
    )
    restful_payload = position_demand.validated_complete_demand()
    assert restful_payload["y"] == 14.9


def test_that_attenuator_position_demand_can_be_created_with_only_one_wheel():
    wedge_position_demands = {}
    wheel_position_demands = {"w": 2}
    position_demand = AttenuatorMotorPositionDemands(
        continuous_demands=wedge_position_demands,
        indexed_demands=wheel_position_demands,
    )
    assert position_demand is not None


def test_that_attenuator_position_demand_with_only_one_wheel_provides_expected_rest_format():
    wedge_position_demands = {}
    wheel_position_demands = {"w": 6}
    position_demand = AttenuatorMotorPositionDemands(
        continuous_demands=wedge_position_demands,
        indexed_demands=wheel_position_demands,
    )
    restful_payload = position_demand.validated_complete_demand()
    assert restful_payload["w"] == 6


def test_that_empty_attenuator_position_demand_can_be_created():
    wedge_position_demands = {}
    wheel_position_demands = {}
    position_demand = AttenuatorMotorPositionDemands(
        continuous_demands=wedge_position_demands,
        indexed_demands=wheel_position_demands,
    )
    assert position_demand is not None


def test_that_empty_attenuator_position_demand_provides_empty_rest_format():
    wedge_position_demands = {}
    wheel_position_demands = {}
    position_demand = AttenuatorMotorPositionDemands(
        continuous_demands=wedge_position_demands,
        indexed_demands=wheel_position_demands,
    )
    restful_payload = position_demand.validated_complete_demand()
    assert restful_payload == {}


def test_that_attenuator_position_demand_triplet_can_be_created():
    standard_wedge_position_demand = {"x": 25.9, "y": 5.0}
    standard_wheel_position_demand = {"w": 4}
    position_demand = AttenuatorMotorPositionDemands(
        continuous_demands=standard_wedge_position_demand,
        indexed_demands=standard_wheel_position_demand,
    )
    assert position_demand is not None


def test_that_attenuator_position_demand_triplet_provides_expected_rest_format():
    wedge_position_demands = {"x": 0.1, "y": 90.1}
    wheel_position_demands = {"w": 6}
    position_demand = AttenuatorMotorPositionDemands(
        continuous_demands=wedge_position_demands,
        indexed_demands=wheel_position_demands,
    )
    restful_payload = position_demand.validated_complete_demand()
    assert restful_payload == {"x": 0.1, "y": 90.1, "w": 6}


# Happy path tests above

# Unhappy path tests below


def test_that_attenuator_position_raises_error_when_discrete_and_continuous_demands_overload_axis_label():
    wedge_position_demands = {"x": 0.1, "v": 90.1}
    wheel_position_demands = {"w": 6, "v": 7}
    anticipated_preamble: str = "1 validation error for AttenuatorMotorPositionDemands"
    with pytest.raises(expected_exception=ValueError, match=anticipated_preamble):
        AttenuatorMotorPositionDemands(
            continuous_demands=wedge_position_demands,
            indexed_demands=wheel_position_demands,
        )


def test_that_attenuator_position_creation_raises_error_when_continuous_position_demand_is_none():
    wedge_position_demands = {"x": None, "y": 90.1}
    wheel_position_demands = {}
    with pytest.raises(expected_exception=ValueError):
        AttenuatorMotorPositionDemands(
            continuous_demands=wedge_position_demands,
            indexed_demands=wheel_position_demands,
        )


def test_that_attenuator_position_creation_raises_error_when_indexed_position_demand_is_none():
    wedge_position_demands = {"x": 14.88, "y": 90.1}
    wheel_position_demands = {"w": None, "v": 3}
    with pytest.raises(expected_exception=ValueError):
        AttenuatorMotorPositionDemands(
            continuous_demands=wedge_position_demands,
            indexed_demands=wheel_position_demands,
        )


def test_that_attenuator_position_creation_raises_error_when_continuous_position_key_is_none():
    wedge_position_demands = {"x": 32.65, None: 80.1}
    wheel_position_demands = {"w": 8}
    with pytest.raises(expected_exception=ValueError):
        AttenuatorMotorPositionDemands(
            continuous_demands=wedge_position_demands,
            indexed_demands=wheel_position_demands,
        )


def test_that_attenuator_position_creation_raises_error_when_indexed_position_key_is_none():
    wedge_position_demands = {"x": 24.08, "y": 71.4}
    wheel_position_demands = {"w": 1, None: 2}
    with pytest.raises(expected_exception=ValueError):
        AttenuatorMotorPositionDemands(
            continuous_demands=wedge_position_demands,
            indexed_demands=wheel_position_demands,
        )
