import copy
from typing import Any, Final

import pytest
from pydantic import ValidationError

from dodal.devices.beamlines.i19.transmission.spec_from_config.lateral_motor_spec import (
    LateralMotorsConfig,
    LateralMotorSpec,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.system_configuration import (
    SystemConfiguration,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.transmission_system_spec import (
    TransmissionSystemSpec,
)
from tests.devices.beamlines.i19.transmission.spec_from_config.fake_json import (
    FAKE_SYSTEM_SPECIFICATION_1_JSON,
    REALISTIC_SYSTEM_SPECIFICATION,
)

JSON1: Final[dict[str, dict[str, Any]]] = REALISTIC_SYSTEM_SPECIFICATION
JSON2: Final[dict[str, dict[str, Any]]] = FAKE_SYSTEM_SPECIFICATION_1_JSON

# happy path tests below


@pytest.mark.parametrize("hardware_parameters", [JSON1, JSON2])
def test_that_lateral_motors_can_be_extracted_from_configuration_blob(
    hardware_parameters: dict[str, dict[str, Any]],
) -> None:
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=hardware_parameters,
    )
    all_motors: dict[str, LateralMotorSpec] = (
        LateralMotorsConfig.get_aspect_specifications(
            system_configuration=_system_config
        )
    )
    for axis, motor_spec in all_motors.items():
        assert motor_spec is not None, f"Lateral motor parameters for {axis} not found."


@pytest.mark.parametrize(
    "hardware_parameters, expected_motor_axes",
    [(JSON1, ["x", "y"]), (JSON2, ["a", "b"])],
)
def test_that_all_lateral_motor_axis_names_can_be_read(
    hardware_parameters: dict[str, dict[str, Any]],
    expected_motor_axes: list[str],
) -> None:
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=hardware_parameters,
    )
    _axes = LateralMotorsConfig.name_all_specified(system_configuration=_system_config)
    assert sorted(_axes) == sorted(expected_motor_axes)


@pytest.mark.parametrize(
    "motor_axis, expected_maximum_position", [("b", 85.2), ("a", 61.0)]
)
def test_that_lateral_motor_specs_have_interrogatable_form(
    motor_axis: str, expected_maximum_position: float
) -> None:
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=JSON2,
    )
    _extracted_motor = LateralMotorsConfig.extract_motors_specifications(
        system_configuration=_system_config, motor_identifier=motor_axis
    )
    _max: float = _extracted_motor.max
    assert _max == pytest.approx(expected=expected_maximum_position)


# Happy path above

# Inauspicious path below


def test_that_lateral_motor_rejects_empty_json_blob() -> None:
    _copied_json = copy.deepcopy(JSON1)
    _null_motor = {"z": {}}
    _copied_json["lateral_motors"] |= _null_motor  # merge in the extra "motor"
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_copied_json,
    )
    with pytest.raises(ValidationError):
        LateralMotorsConfig.get_aspect_specifications(
            system_configuration=_system_config
        )


# typo here max <- Max
TYPO_MOTOR: Final[dict[str, Any]] = {
    "t": {
        "units": "mm",
        "out": 0.19,
        "threshold": 13.5,
        "Max": 81.0,
        "tolerance": 5.0e-3,
    },
}


def test_that_motor_json_blob_is_rejected_with_typo() -> None:
    _copied_json = copy.deepcopy(JSON1)
    _copied_json["lateral_motors"] |= TYPO_MOTOR  # merge in the new motor entry
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_copied_json,
    )
    with pytest.raises(ValidationError):
        LateralMotorsConfig.get_aspect_specifications(
            system_configuration=_system_config
        )


# out position is mid wedge - so invalid
INVALID_MOTOR_1: Final[dict[str, Any]] = {
    "t": {
        "units": "mm",
        "out": 49.065,
        "threshold": 13.5,
        "max": 81.0,
        "tolerance": 5.0e-3,
    },
}

# out position is mid wedge - so invalid
INVALID_MOTOR_2: Final[dict[str, Any]] = {
    "t": {
        "units": "mm",
        "out": -29.134,
        "threshold": -19.5,
        "max": -58.4,
        "tolerance": 5.0e-3,
    },
}


@pytest.mark.parametrize("invalid_motor", [INVALID_MOTOR_1, INVALID_MOTOR_2])
def test_that_invalid_motor_is_rejected(
    invalid_motor: dict[str, dict[str, Any]],
) -> None:
    _copied_json = copy.deepcopy(JSON1)
    _copied_json["lateral_motors"] |= INVALID_MOTOR_1  # merge in the new motor entry
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_copied_json,
    )
    with pytest.raises(ValidationError):
        LateralMotorsConfig.get_aspect_specifications(
            system_configuration=_system_config
        )


@pytest.mark.parametrize(
    "invalid_axis_name",
    (
        "",
        "!",
        "-4.2",
        "5.8",
        "7",
        "+1",
        " ",
        "+x",
        "_3",
        "-62",
        "Hg/Pb",
        "£3.75",
        "Aluminium.alloy",
        "Zr€",
        "99flake",
        " - ",
        "per: Capita",
    ),
)
def test_that_motor_json_blob_is_rejected_without_valid_axis_name(
    invalid_axis_name: str,
) -> None:
    _misnamed_motor: Final[dict[str, Any]] = {
        invalid_axis_name: {
            "units": "mm",
            "out": 5.87,
            "threshold": 13.5,
            "max": 60.78,
            "tolerance": 5.0e-3,
        },
    }
    _copied_json = copy.deepcopy(JSON1)
    _copied_json["lateral_motors"] |= _misnamed_motor
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_copied_json,
    )
    with pytest.raises(ValidationError):
        LateralMotorsConfig.get_aspect_specifications(
            system_configuration=_system_config
        )
