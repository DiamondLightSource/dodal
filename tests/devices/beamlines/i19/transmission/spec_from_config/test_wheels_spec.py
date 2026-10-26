import copy
from collections.abc import Iterable
from typing import Any, Final

import pytest
from pydantic import ValidationError

from dodal.devices.beamlines.i19.transmission.spec_from_config.system_configuration import (
    SystemConfiguration,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.transmission_system_spec import (
    TransmissionSystemSpec,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.wheels_spec import (
    WheelsConfig,
)
from tests.devices.beamlines.i19.transmission.spec_from_config.fake_json import (
    FAKE_SYSTEM_SPECIFICATION_1_JSON,
    REALISTIC_SYSTEM_SPECIFICATION,
)
from tests.devices.beamlines.i19.transmission.spec_from_config.utility_constants import (
    NON_NUMERICALS,
)

JSON1: Final[dict[str, dict[str, Any]]] = REALISTIC_SYSTEM_SPECIFICATION
JSON2: Final[dict[str, dict[str, Any]]] = FAKE_SYSTEM_SPECIFICATION_1_JSON


# Utility method tp prepare extracted lists etc ready for comparison with expectations.
def _convert_and_sort(original: Iterable[Any]) -> list[int]:
    _integerised = [int(s) for s in original]
    return sorted(_integerised)


def both_list_identical_integers(a: Iterable[Any], b: Iterable[Any]) -> bool:
    return _convert_and_sort(a) == _convert_and_sort(b)


@pytest.mark.parametrize(
    "hardware_parameters, expected_foils",
    [
        (
            JSON1,
            ["2", "4", "6"],
        ),
        (
            JSON2,
            ["1", "3", "4", "6"],
        ),
    ],
)
def test_that_wheel_spec_correctly_captures_represents_slot_occupancy(
    hardware_parameters: dict[str, dict[str, Any]], expected_foils: list[str]
) -> None:
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=hardware_parameters,
    )
    _wheel_config = WheelsConfig.extract_wheel_specifications(
        system_configuration=_system_config, wheel_identifier="w"
    )
    _foils_present = _wheel_config.foils.keys()
    assert both_list_identical_integers(_foils_present, expected_foils)


@pytest.mark.parametrize(
    "hardware_parameters, expected_out_slot",
    [
        (JSON1, 1),
        (JSON2, 5),
    ],
)
def test_that_wheel_spec_correctly_captures_slot_used_for_out_position(
    hardware_parameters: dict[str, dict[str, Any]], expected_out_slot: int
) -> None:
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=hardware_parameters,
    )
    _wheel_config = WheelsConfig.extract_wheel_specifications(
        system_configuration=_system_config, wheel_identifier="w"
    )
    _out_position = _wheel_config.out
    assert _out_position == expected_out_slot


@pytest.mark.parametrize(
    "hardware_parameters, expected_permitted_slots",
    [
        (JSON1, [1]),
        (JSON2, [5, 3, 4]),
    ],
)
def test_that_wheel_spec_correctly_captures_slot_permissions(
    hardware_parameters: dict[str, dict[str, Any]], expected_permitted_slots: list[int]
) -> None:
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=hardware_parameters,
    )
    _wheel_config = WheelsConfig.extract_wheel_specifications(
        system_configuration=_system_config, wheel_identifier="w"
    )

    assert both_list_identical_integers(
        _wheel_config.permissions, expected_permitted_slots
    )


# Happy tests above

# Inauspicious tests below


@pytest.mark.parametrize(
    "invalid_out_slot",
    NON_NUMERICALS,
)
def test_that_wheel_spec_raises_error_if_out_slot_is_invalid(
    invalid_out_slot: Any,
) -> None:
    _fake_json = copy.deepcopy(JSON1)
    _fake_json["wheels"]["w"]["out"] = invalid_out_slot
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_fake_json,
    )
    with pytest.raises(ValidationError):
        _wheel_config = WheelsConfig.extract_wheel_specifications(
            system_configuration=_system_config, wheel_identifier="w"
        )


@pytest.mark.parametrize(
    "json",
    [JSON1, JSON2],
)
def test_that_wheel_spec_correctly_raises_error_if_out_slot_is_absent(
    json: dict[str, dict[str, Any]],
) -> None:
    _fake_json = copy.deepcopy(json)
    _fake_json["wheels"]["w"].pop("out", None)
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_fake_json,
    )
    with pytest.raises(ValidationError):
        _wheel_config = WheelsConfig.extract_wheel_specifications(
            system_configuration=_system_config, wheel_identifier="w"
        )


@pytest.mark.parametrize(
    "json",
    [JSON1, JSON2],
)
def test_that_wheel_spec_correctly_raises_error_if_slot_permissions_empty(
    json: dict[str, dict[str, Any]],
) -> None:
    _fake_json = copy.deepcopy(json)
    _fake_json["wheels"]["w"]["permissions"] = []
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_fake_json,
    )
    with pytest.raises(ValidationError):
        _wheel_config = WheelsConfig.extract_wheel_specifications(
            system_configuration=_system_config, wheel_identifier="w"
        )
