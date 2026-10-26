import copy
import math
from typing import Any

import pytest
from pydantic import ValidationError

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

JSON1: dict[str, dict[str, Any]] = REALISTIC_SYSTEM_SPECIFICATION
JSON2: dict[str, dict[str, Any]] = FAKE_SYSTEM_SPECIFICATION_1_JSON

# happy path test


@pytest.mark.parametrize(
    "hardware_parameters",
    [JSON1, JSON2],
)
def test_that_system_config_can_wrap_valid_configuration_dict(
    *,
    hardware_parameters: dict[str, Any],
) -> None:
    _wrapped_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=hardware_parameters,
    )
    assert _wrapped_config is not None


# happy path test above

# inauspicious path tests below


@pytest.mark.parametrize(
    "invalid_dict",
    [
        True,
        False,
        0,
        8.4,
        -13.2 - 9,
        {"a", "nope"},
        math.exp,
        object(),
        None,
        KeyError(),
    ],
)
def test_that_invalid_hardware_parameters_raise_error_when_wrapped(
    *,
    invalid_dict: Any,
) -> None:
    with pytest.raises(ValidationError):
        _wrapped_config: SystemConfiguration = SystemConfiguration(
            structural_template=TransmissionSystemSpec,
            hardware_parameters=invalid_dict,
        )


@pytest.mark.parametrize(
    "sub_dict_name", ["materials", "lateral_motors", "wedges", "wheels"]
)
@pytest.mark.parametrize(
    "invalid_dict",
    [
        {"a", None},
        True,
        False,
        0,
        8.4,
        -13.2,
        -9,
        {"a", "nope"},
        math.atan2,
        object(),
        None,
        KeyError(),
    ],
)
def test_that_test_that_config_validation_raises_error_when_subdict_is_invalid(
    invalid_dict,
    sub_dict_name,
) -> None:
    _copied_json = copy.deepcopy(JSON1)
    _copied_json[sub_dict_name] = invalid_dict
    with pytest.raises(ValidationError):
        _system_config: SystemConfiguration = SystemConfiguration(
            structural_template=TransmissionSystemSpec,
            hardware_parameters=_copied_json,
        )
