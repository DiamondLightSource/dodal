"""Provides functions to convert between common units for attenuation."""

from numpy.polynomial import polynomial
from pydantic import StrictFloat, validate_call

from dodal.common.general_maths.interval import ClosedInterval, DirectedSegment


@validate_call
def convert_percentage_to_factor(pc: StrictFloat) -> float:
    """Takes a percentage value and converts it the corresponding multiplication factor.

    Args:
        pc (StrictFloat): a percentage
    Returns:
        pc (float): a factor
    """
    return pc * 1e-2


@validate_call
def convert_factor_to_percentage(f: StrictFloat) -> float:
    """Takes a multiplication factor and converts it to the corresponding percentage.

    Args:
        f (StrictFloat): a factor

    Returns:
        f (float): a percentage
    """
    return f * 1e2


@validate_call
def convert_microns_to_cm(t_um: StrictFloat) -> float:
    """Takes the numerical part of a distance in microns and converts this to cm.

    Args:
        t_um (StrictFloat): a distance in microns

    Returns:
        t_um (float): a distance in cm
    """
    return t_um * 1e-4


@validate_call
def convert_microns_to_mm(v_um: StrictFloat) -> float:
    """Takes the numerical part of a distance in microns and converts this to mm.

    Args:
        v_um (StrictFloat): a distance in microns

    Returns:
        v_um (float): a distance in mm
    """
    return v_um * 1e-3


@validate_call
def convert_mm_to_microns(w_mm: StrictFloat) -> float:
    """Takes the numerical part of a distance in mm and converts this to microns.

    Args:
        w_mm (StrictFloat): a distance in mm

    Returns:
        w_um (float): a distance in microns
    """
    return w_mm * 1e3


@validate_call
def convert_mm_to_cm(x_mm: StrictFloat) -> float:
    """Takes the numerical part of a distance in mm and converts this to cm.

    Args:
        x_mm (StrictFloat): a distance in mm

    Returns:
        w_um (float): a distance in cm
    """
    return x_mm * 1e-1


@validate_call
def convert_cm_to_mm(y_cm: StrictFloat) -> float:
    """Takes the numerical part of a distance in cm and converts this to mm.

    Args:
        y_cm (StrictFloat): a distance in cm

    Returns:
        w_um (float): a distance in mm
    """
    return y_cm * 1e1


@validate_call
def convert_ev_to_kev(energy_ev: StrictFloat) -> float:
    """Takes the numerical part of an x-ray energy in electron volts and converts this
    to keV.

    Args:
        energy_ev (StrictFloat): a value of electron volts

    Returns:
        energy_ev (float): a value of kilo-electron volts
    """
    return energy_ev * 1e-3


@validate_call
def get_straight_line_y(
    line_offset: StrictFloat, line_gradient: StrictFloat, x: StrictFloat
) -> float:
    """Convenient internal conversion method which delegates to numpy for a 1st order polynomial (line).

    The traditional y = mx + c to compute y.

    Args:
        line_offset: the offset, where the modelled line intercepts the abscissa.
        line_gradient: the gradient of the modelled line
        x: the input coordinate of the point on the line, from which y is computed.
    """
    _coefficients = [line_offset, line_gradient]
    _y = polynomial.polyval(x, _coefficients)
    return float(_y)

INTERPOLATION_FRACTIONAL_RANGE = ClosedInterval(lower=0.0, upper=1.0)

@validate_call
def parametrised_value(
    normalising_directed_segment: DirectedSegment,
    parametric_fraction: StrictFloat,
    strictly_interpolation=True,
) -> float:
    """Select, using a parametric fraction, one point off a linear mapping, taking start and scale from an interval.

    Args:
        segment: Directed segment representing directional unit distance, with a defined start.
        parametric_fraction: The governing parameter which selects where along (or outside) the interval to select.
        strictly_interpolation: If True causes errors to be raised when the fraction is outside 0 to 1.

    Returns:
        A value interpolated / extrapolated away from the segment's start.

    Note:
        Results from negative input fractions can be counter-intuitive.

    Example:
        A directed segment from +10 to +12, using a fraction of +0.5 will result in +11.
        The same directed segment (with strict set to False) converts fractions of 0, +1, -1 into +10, +12 and +8 respectively.
    """
    if strictly_interpolation and parametric_fraction not in INTERPOLATION_FRACTIONAL_RANGE:
        raise ValueError(
            "Cannot strictly interpolate for parameterised position outside interval"
        )
    return get_straight_line_y(
        line_offset=normalising_directed_segment.start,
        line_gradient=normalising_directed_segment.span,
        x=parametric_fraction
    )


@validate_call
def parametric_fraction(normalising_directed_segment: DirectedSegment, value: StrictFloat) -> float:
    """Find the equivalent fractional (normalised) distance along an interval of any real value.

    Args:
        normalising_directed_segment: Directed unit displacement, from a defined start.
        value: The real to convert.

    Returns:
        A fraction after reverse interpolating / extrapolating the fraction away from the interval's lower bound.

    Note:
        The results for values below the interval's lower endpoint can be counter-intuitive.

    Example:
        An interval from +10 to +12, a value of +11 corresponds to a fractional output of +0.5.
        The same interval converts values of -6, +10, +20 into -8.0, 0.0 and +5.0 respectively.
    """
    reciprocal_of_span = 1.0 / normalising_directed_segment.span
    return get_straight_line_y(
        line_offset=-reciprocal_of_span * normalising_directed_segment.start,
        line_gradient=reciprocal_of_span,
        x=value,
    )
