import math

import pydantic
import pytest

from dodal.common.general_maths.absorber_geometry import FoilGeometry, WedgeGeometry

# happy path


@pytest.mark.parametrize(
    "distance_unit, numerical_thickness_in_specified_unit, expected_thickness_cm",
    [
        ("cm", 0.193, 0.193),
        ("um", 150.0, 0.015),
        ("mm", 4.2, 0.42),
        ("micron", 812.5, 0.08125),
    ],
)
def test_foil_absorber_reports_thickness_in_cm_when_validly_specified(
    distance_unit, numerical_thickness_in_specified_unit, expected_thickness_cm
):
    flat_absorber = FoilGeometry(
        unit=distance_unit, numerical_value=numerical_thickness_in_specified_unit
    )
    assert flat_absorber.get_thickness_cm() == pytest.approx(expected_thickness_cm)


@pytest.mark.parametrize(
    "tip, taper_cotangent, probed_position_mm, expected_thickness_cm",
    [
        (-5.0, 10.0, -5.0, 0.0),
        (2.0, -10.0, -15.2, 0.172),
        (-12.8, 9.7, 80.6, 0.9628866),
        (12.8, 11.1, 22.4, 0.08648649),
    ],
)
def test_wedge_geometry_reports_correct_thickness_in_cm(
    tip, taper_cotangent, probed_position_mm, expected_thickness_cm
):
    wedge_absorber = WedgeGeometry(tip_mm=tip, taper_cotangent=taper_cotangent)
    assert wedge_absorber.thickness_cm_at_motor_position_mm(
        probed_position_mm
    ) == pytest.approx(expected_thickness_cm)


@pytest.mark.parametrize(
    "tip, taper_cotangent, required_thickness_cm, expected_motor_position_mm",
    [
        (-5.0, 10.0, 0.04, -1.0),
        (2.0, -10.0, 0.172, -15.2),
        (-12.8, 9.7, 0.9628866, 80.6),
        (12.8, 11.1, 0.08648649, 22.4),
    ],
)
def test_wedge_geometry_reports_correct_motor_position_mm_to_achieve_requested_thickness(
    tip, taper_cotangent, required_thickness_cm, expected_motor_position_mm
):
    wedge_absorber = WedgeGeometry(tip_mm=tip, taper_cotangent=taper_cotangent)
    assert wedge_absorber.motor_position_mm_for_thickness_cm(
        required_thickness_cm
    ) == pytest.approx(expected_motor_position_mm)


# inauspicious path


@pytest.mark.parametrize(
    "bad_input",
    [
        "",
        "k",
        math.cos,
        None,
        [],
        {},
        object(),
        False,
    ],
)
def test_foil_absorber_raises_error_when_given_invalid_input_for_numerical_thickness(
    bad_input,
):
    with pytest.raises(pydantic.ValidationError):
        FoilGeometry(unit="cm", numerical_value=bad_input)


@pytest.mark.parametrize(
    "unsupported_unit",
    [
        "",
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
    unsupported_unit,
):
    with pytest.raises(KeyError):
        FoilGeometry(unit=unsupported_unit, numerical_value=1.1)


@pytest.mark.parametrize(
    "bad_input",
    [
        -9,
        4.7,
        math.sin,
        None,
        [],
        {},
        object(),
        True,
    ],
)
def test_foil_absorber_raises_error_when_given_invalid_distance_units(bad_input):
    with pytest.raises(pydantic.ValidationError):
        FoilGeometry(unit=bad_input, numerical_value=1.1)


@pytest.mark.parametrize(
    "taper_cotangent",
    [
        0.0,
        1.0,
        -2.1,
        0.03,
        4.58,
        1.16,
    ],
)
def test_wedge_absorber_raises_error_when_given_chunky_wedge_angle(taper_cotangent):
    with pytest.raises(pydantic.ValidationError):
        WedgeGeometry(tip_mm=4.8, taper_cotangent=taper_cotangent)


@pytest.mark.parametrize(
    "bad_input",
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
def test_wedge_absorber_raises_error_when_given_invalid_input_for_taper(bad_input):
    with pytest.raises(pydantic.ValidationError):
        WedgeGeometry(tip_mm=3.17, taper_cotangent=bad_input)


@pytest.mark.parametrize(
    "bad_input",
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
    bad_input,
):
    with pytest.raises(pydantic.ValidationError):
        WedgeGeometry(tip_mm=bad_input, taper_cotangent=-7.6)
