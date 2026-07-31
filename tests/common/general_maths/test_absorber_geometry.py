import math
from typing import Any, Literal

import pydantic
import pytest

from dodal.common.general_maths.absorber_geometry import FoilGeometry, WedgeGeometry

# happy path


@pytest.mark.parametrize(
    "_distance_unit, _numerical_thickness_in_specified_unit, _expected_thickness_cm",
    [
        ("cm", 0.193, 0.193),
        ("um", 150.0, 0.015),
        ("mm", 4.2, 0.42),
        ("micron", 812.5, 0.08125),
    ],
)
def test_foil_absorber_reports_thickness_in_cm_when_validly_specified(
    _distance_unit: str,
    _numerical_thickness_in_specified_unit: float,
    _expected_thickness_cm: float,
) -> None:
    flat_absorber = FoilGeometry(
        unit=_distance_unit, numerical_value=_numerical_thickness_in_specified_unit
    )
    assert flat_absorber.get_thickness_cm() == pytest.approx(_expected_thickness_cm)


@pytest.mark.parametrize(
    "_tip, _taper_cotangent, _probed_position_mm, _expected_thickness_cm",
    [
        (-5, 5.0, -5.0, 0.0),
        (2, -10.0, -15.2, 0.172),
        (-12.8, 9.7, 80.6, 0.9628866),
        (12.8, 11.1, 22.4, 0.08648649),
    ],
)
def test_wedge_geometry_reports_correct_thickness_in_cm(
    _tip: float | Literal[-5] | Literal[2],
    _taper_cotangent: float,
    _probed_position_mm: float,
    _expected_thickness_cm: float,
) -> None:
    wedge_absorber = WedgeGeometry(tip_mm=_tip, taper_cotangent=_taper_cotangent)
    assert wedge_absorber.thickness_cm_at_motor_position_mm(
        motor_position_mm=_probed_position_mm
    ) == pytest.approx(_expected_thickness_cm)


@pytest.mark.parametrize(
    "_tip, _taper_cotangent, _required_thickness_cm, _expected_motor_position_mm",
    [
        (-5.0, 10.0, 0.04, -1.0),
        (3, -10.0, 0.172, -14.2),
        (-12.8, 9.7, 0.9628866, 80.6),
        (12.8, 11.1, 0.08648649, 22.4),
    ],
)
def test_wedge_geometry_reports_correct_motor_position_mm_to_achieve_requested_thickness(
    _tip: float | Literal[3],
    _taper_cotangent: float,
    _required_thickness_cm: float,
    _expected_motor_position_mm: float,
) -> None:
    wedge_absorber = WedgeGeometry(tip_mm=_tip, taper_cotangent=_taper_cotangent)
    assert wedge_absorber.motor_position_mm_for_thickness_cm(
        thickness_cm=_required_thickness_cm
    ) == pytest.approx(_expected_motor_position_mm)


# inauspicious path


@pytest.mark.parametrize(
    "_bad_number",
    [
        "",
        "k",
        math.cos,
        None,
        [],
        {},
        object(),
        AttributeError(),
        False,
        True,
    ],
)
def test_foil_absorber_raises_error_when_given_invalid_input_for_numerical_thickness(
    _bad_number: Any,
):
    with pytest.raises(pydantic.ValidationError):
        FoilGeometry(unit="cm", numerical_value=_bad_number)


@pytest.mark.parametrize(
    "_unsupported_unit",
    [
        "",
        "12",
        "mile",
        "km",
        "furlong",
        "yard",
        "ft",
        "lb",
        "s",
        "Bq",
        "A",
        "eV",
    ],
)
def test_foil_absorber_raises_error_when_asked_to_use_unsupported_distance_units(
    _unsupported_unit: Any,
):
    with pytest.raises(KeyError):
        FoilGeometry(unit=_unsupported_unit, numerical_value=1.1)


@pytest.mark.parametrize(
    "_bad_input",
    [
        -9,
        0,
        4.7,
        math.sin,
        None,
        [],
        {},
        object(),
        KeyError(),
        True,
        False,
    ],
)
def test_foil_absorber_raises_error_when_given_invalid_distance_units(
    _bad_input: Any,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        FoilGeometry(unit=_bad_input, numerical_value=1.1)


@pytest.mark.parametrize(
    "_taper_cotangent",
    [
        0,
        1,
        -2,
        4,
        -3,
        0.0,
        1.0,
        -2.1,
        0.03,
        4.58,
        1.16,
    ],
)
def test_wedge_absorber_raises_error_when_given_chunky_wedge_angle(
    _taper_cotangent: float,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        WedgeGeometry(tip_mm=4.8, taper_cotangent=_taper_cotangent)


@pytest.mark.parametrize(
    "_bad_input",
    [
        "",
        "k",
        math.cos,
        None,
        [],
        {},
        object(),
        True,
    ],
)
def test_wedge_absorber_raises_error_when_given_invalid_input_for_taper(
    _bad_input: Any,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        WedgeGeometry(tip_mm=3.17, taper_cotangent=_bad_input)


@pytest.mark.parametrize(
    "_bad_input",
    [
        "",
        "k",
        math.cos,
        None,
        [],
        {},
        object(),
        True,
    ],
)
def test_wedge_absorber_raises_error_when_given_invalid_input_for_tip_position(
    _bad_input: Any,
):
    with pytest.raises(pydantic.ValidationError):
        WedgeGeometry(tip_mm=_bad_input, taper_cotangent=-7.6)
