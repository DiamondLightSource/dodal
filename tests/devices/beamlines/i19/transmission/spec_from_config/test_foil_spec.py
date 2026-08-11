import math
from typing import Any

import pytest
from pydantic import ValidationError

from dodal.devices.beamlines.i19.transmission.spec_from_config.foil_spec import FoilSpec

# Happy path tests


@pytest.mark.parametrize(
    "valid_foil_parameters",
    [
        {"absorber": {"material": "iron", "thickness": {"units": "um", "value": 98.6}}},
        {
            "absorber": {
                "material": "gold",
                "thickness": {"units": "um", "value": 14.08},
            }
        },
    ],
)
def test_that_foil_spec_can_be_instantiated_from_valid_dict(
    valid_foil_parameters: dict[str, Any],
) -> None:
    _foil = FoilSpec.model_validate(valid_foil_parameters)
    assert _foil is not None


# Happy path tests above


# Inauspicious path tests below


@pytest.mark.parametrize(
    "invalid_dict",
    [
        True,
        False,
        0,
        8.4,
        -13.2 - 9,
        {"a", "nope"},
        math.log1p,
        object(),
        None,
        KeyError(),
    ],
)
def test_that_foil_spec_raises_error_when_dict_is_invalid(invalid_dict) -> None:
    with pytest.raises(ValidationError):
        FoilSpec.model_validate(invalid_dict)
