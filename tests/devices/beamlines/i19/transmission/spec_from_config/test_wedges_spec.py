import copy
import math
from typing import Any, Final

import pytest
from pydantic import ValidationError

from dodal.devices.beamlines.i19.transmission.spec_from_config.system_configuration import (
    SystemConfiguration,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.transmission_system_spec import (
    TransmissionSystemSpec,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.wedges_spec import (
    WedgesConfig,
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


@pytest.mark.parametrize(
    "hardware_parameters, wedge_identifier",
    [
        (
            JSON1,
            "y",
        ),
        (
            JSON2,
            "a",
        ),
    ],
)
def test_that_wedges_config_can_be_constructed_from_valid_populated_dict(
    *, hardware_parameters: dict[str, dict[str, Any]], wedge_identifier: str
) -> None:
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=hardware_parameters,
    )
    _wedge_spec = WedgesConfig.get_aspect_specifications(
        system_configuration=_system_config
    )
    for wedge in _wedge_spec.keys():
        assert _wedge_spec[wedge] is not None


# Note an absence of wedges should not invalidate the configuration
#  - what if the motors are being repaired and we just want to use filter wheels for now
# That scenario should be supported!


@pytest.mark.parametrize(
    "hardware_parameters",
    [JSON1, JSON2],
)
def test_that_wedges_config_can_validly_represent_absence(
    hardware_parameters: dict[str, dict[str, Any]],
) -> None:
    _copied_json = copy.deepcopy(hardware_parameters)
    _copied_json["wedges"] = {}
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_copied_json,
    )
    _wedges_config = WedgesConfig._extract_system_aspect(
        system_configuration=_system_config
    )
    assert _wedges_config is not None


@pytest.mark.parametrize(
    "hardware_parameters, wedge_with_voids",
    [
        (
            JSON1,
            "x",
        ),
        (
            JSON2,
            "a",
        ),
    ],
)
def test_that_wedges_config_parses_correct_interval_for_voids(
    hardware_parameters: dict[str, dict[str, Any]],
    wedge_with_voids: str,
) -> None:
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=hardware_parameters,
    )
    _wedge_spec = WedgesConfig.extract_wedge_specifications(
        system_configuration=_system_config, wedge_identifier=wedge_with_voids
    )
    # check void straddles a known bubbly position
    _known_bubble_point = 17.89
    _wedge_geometry = _wedge_spec.geometry
    _first_bubble_void = _wedge_geometry.voids[0]
    assert _known_bubble_point in _first_bubble_void


# happy path tests above

# inauspicious path tests


@pytest.mark.parametrize(
    "invalid_cotangent",
    NON_NUMERICALS,
)
@pytest.mark.parametrize("wedge", ["x", "y"])
def test_that_wedge_spec_raises_error_when_cotangent_is_invalid(
    wedge: str,
    invalid_cotangent: Any,
) -> None:
    _fake_json = copy.deepcopy(JSON1)
    _fake_json["wedges"][wedge]["geometry"]["cotangent"] = invalid_cotangent
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_fake_json,
    )
    with pytest.raises(ValidationError):
        _wedge_config = WedgesConfig.extract_wedge_specifications(
            system_configuration=_system_config,
            wedge_identifier=wedge,
        )


@pytest.mark.parametrize(
    "invalid_tip",
    NON_NUMERICALS,
)
@pytest.mark.parametrize("wedge", ["x", "y"])
def test_that_wedge_spec_raises_error_when_tip_is_invalid(
    wedge: str,
    invalid_tip: Any,
) -> None:
    _fake_json = copy.deepcopy(JSON1)
    _fake_json["wedges"][wedge]["geometry"]["tip"] = invalid_tip
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_fake_json,
    )
    with pytest.raises(ValidationError):
        _wedge_config = WedgesConfig.extract_wedge_specifications(
            system_configuration=_system_config,
            wedge_identifier=wedge,
        )


# deliberate typos
# first entry for material -> Naterial
# second entry for geometry -> gOEmetry


@pytest.mark.parametrize(
    "hardware_parameters, wedge, good_key, typo_key",
    [
        (
            JSON1,
            "y",
            "material",
            "naterial",
        ),
        (
            JSON2,
            "b",
            "geometry",
            "goemetry",
        ),
    ],
)
def test_that_system_config_with_typo_in_key_raises_error(
    hardware_parameters: dict[str, dict[str, Any]],
    wedge: str,
    good_key: str,
    typo_key: str,
) -> None:
    _copied_json = copy.deepcopy(hardware_parameters)
    _corruptable_wedge_sub_dict = _copied_json["wedges"][wedge]
    _corruptable_wedge_sub_dict[typo_key] = _corruptable_wedge_sub_dict.pop(good_key)

    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_copied_json,
    )
    with pytest.raises(ValidationError):
        _wedge_config = WedgesConfig.extract_wedge_specifications(
            system_configuration=_system_config,
            wedge_identifier=wedge,
        )


@pytest.mark.parametrize(
    "invalid_voids",
    [
        "Neither a list nor a dict",
        "[16.2,25.3]",
        -4.2,
        88,
        math.pi,
        -12,
        True,
        False,
        ValueError(),
        object(),
        math.log,
    ],
)
def test_that_wedge_specifying_voids_using_incorrect_type_is_rejected(
    invalid_voids: Any,
) -> None:
    _copied_json = copy.deepcopy(JSON1)
    _corruptable_geometry = _copied_json["wedges"]["x"]["geometry"]
    _corruptable_geometry["voids"] = (
        invalid_voids  # string is not allowed to specify voids
    )
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_copied_json,
    )
    with pytest.raises(ValidationError):
        _wedge_config = WedgesConfig.get_aspect_specifications(
            system_configuration=_system_config,
        )
