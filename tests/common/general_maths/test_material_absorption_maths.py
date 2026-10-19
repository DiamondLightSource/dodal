import math
from typing import Any, Final, cast
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from dodal.common.general_maths.interval import (
    ClosedInterval,
)
from dodal.common.general_maths.material_absorption_maths import (
    AbsorptionCalculator,
    AbsorptionSpectrumSegment,
    CompoundAbsorptionCalculator,
    MaterialAbsorptionSpectrum,
    PolynomialAbsorptionCorrection,
    SingleRollOffAbsorptionCalculator,
    attenuation_at_depth_cm,
    photon_mass_attenuation_per_unit_length,
    thickness_cm_required_to_attenuate,
)

# happy path


# N.B. the mathematical validity of results from a simple absorption calculator
# are not tested here - since that would duplicate the validatity tests of numerical calculations
# already checked against the photon_mass_attenuation function
@patch(
    "dodal.common.general_maths.material_absorption_maths.photon_mass_attenuation_per_unit_length"
)
def test_simple_absorption_calculator_invokes_photon_mass_attenuation_calculator(
    mock_pma_calc: MagicMock,
) -> None:
    _material_factor = 3.1415926
    _roll_off = -2.71828
    calculator = SingleRollOffAbsorptionCalculator(
        material_factor_per_cm=_material_factor, roll_off=_roll_off
    )
    _x_ray_kev = 15.6302
    calculator.absorption_coefficient_per_cm(energy_kev=_x_ray_kev)
    mock_pma_calc.assert_called_once_with(
        energy_kev=_x_ray_kev,
        photon_absorption_factor_per_unit_length=_material_factor,
        energy_dependence_exponent=_roll_off,
    )


# N.B. the mathematical validity of results from a compound absorption calculator
# are not tested here - since that would duplicate the validatity tests of numerical calculations
# already checked against the contributing calculators within
def test_compound_absorption_calculator_invokes_contributing_calculators() -> None:
    mock_calcs: list[MagicMock] = [
        MagicMock(spec=AbsorptionCalculator),
        MagicMock(spec=AbsorptionCalculator),
    ]
    calcs = cast(list[AbsorptionCalculator], mock_calcs)
    compound_calculator = CompoundAbsorptionCalculator(contributions=calcs)
    _x_ray_kev = 12.6039
    compound_calculator.absorption_coefficient_per_cm(energy_kev=_x_ray_kev)
    for mocked_calculator in mock_calcs:
        mocked_calculator.absorption_coefficient_per_cm.assert_called_once_with(
            energy_kev=_x_ray_kev
        )


@pytest.mark.parametrize(
    "_energy_kev, _polynomial_coefficients, _expected_absorption_coefficient",
    [
        (
            8.3328,
            [50.9211, -23.6148, 4.2138, -0.3814, 1.867e-2, -4.709e-4, 4.796e-6],
            -1.24317951,
        ),
        (
            12.3984,
            [43.4, -22.8148, 4.138, -0.3714, 1.967e-2, -5.709e-4, 3.796e-6],
            0.11254471963,
        ),
        (
            11.9187,
            [50.9211, -23.6148, 4.2138, -0.3814, 1.867e-2, -4.709e-4, 4.796e-6],
            -0.45286288,
        ),
    ],
)
def test_corrective_polynomial_absorption_calculator(
    _energy_kev, _polynomial_coefficients, _expected_absorption_coefficient
) -> None:
    corrective_calculator = PolynomialAbsorptionCorrection(
        coefficients_per_cm=_polynomial_coefficients
    )
    assert corrective_calculator.absorption_coefficient_per_cm(
        energy_kev=_energy_kev
    ) == pytest.approx(_expected_absorption_coefficient)


@pytest.mark.parametrize(
    "_energy_kev, _photon_absorption_factor_per_unit_length, _energy_dependence_exponent,"
    "_result",
    [
        (5.042, 1.98e2, -2.717, 2.44170544),  # At an arbitrary energy 5.042 keV
        (8.3328, 2.5706e3, -2.83, 6.3708311),  # Nickel energy 8.3328 keV
        (11.9187, 1.48e3, -2.93, 1.03970725),  # Gold-Three energy 11.9187 keV
        (25.514, 6.48e3, -2.41, 2.63778077),  # Silver energy 25.514 keV
        (
            20,
            1201,
            -2,
            3.0025,
        ),  # 20 keV: Test that integers, for input args, are not rejected
    ],
)
def test_photon_mass_attenuation_per_unit_length(
    _energy_kev,
    _photon_absorption_factor_per_unit_length,
    _energy_dependence_exponent,
    _result,
) -> None:
    assert photon_mass_attenuation_per_unit_length(
        energy_kev=_energy_kev,
        photon_absorption_factor_per_unit_length=_photon_absorption_factor_per_unit_length,
        energy_dependence_exponent=_energy_dependence_exponent,
    ) == pytest.approx(_result)


@pytest.mark.parametrize(
    "_target_attenuation_bn, _absorption_coefficient_per_cm, _required_cm",
    [
        (0, 2.4, 0),  # test that attenuator thickness required for transparency is zero
        (
            248.461,
            2.13,
            0.1166483568,
        ),  # test attenuator thickness required for arbitrary attenuation
        (
            248.461,
            2.03,
            0.12239458,
        ),  # test that greater attenuator thickness is needed when material absorbs less
        (
            448.641,
            2.13,
            0.21062958,
        ),  # test that greater attenuator thickness is needed to achieve more attenuation
    ],
)
def test_thickness_cm_required_to_attenuate(
    _target_attenuation_bn, _absorption_coefficient_per_cm, _required_cm
) -> None:
    assert thickness_cm_required_to_attenuate(
        _target_attenuation_bn, _absorption_coefficient_per_cm
    ) == pytest.approx(_required_cm, rel=1e-6)


@pytest.mark.parametrize(
    "_depth_cm, _absorption_coefficient_per_cm, _result",
    [
        (
            0.5,
            2,
            1000,
        ),  # tests attenuation is 1 kilobarnett at single attenuation length
        (
            1.89,
            0.316,
            597.24,
        ),  # tests attenuation matches expectations at arbitrary attenuation depth
        (0.0, 2.5, 0),  # tests attenuation is zero after zero depth
    ],
)
def test_attenuation_at_depth_cm(
    _depth_cm, _absorption_coefficient_per_cm, _result
) -> None:
    assert attenuation_at_depth_cm(
        _depth_cm, _absorption_coefficient_per_cm
    ) == pytest.approx(_result, rel=1e-6)


@pytest.mark.parametrize(
    "_lower,_upper", [(12.1, 21.9), (4.8, 49.67), (0.1, 20.01), (15, 31)]
)
def test_single_band_material_absorption_spectrum_performs_in_band_calculation(
    _lower: float, _upper: float
) -> None:
    _energy_interval: ClosedInterval = ClosedInterval(lower=_lower, upper=_upper)
    _calculator: AbsorptionCalculator = SingleRollOffAbsorptionCalculator(
        material_factor_per_cm=1234.5, roll_off=-1.84
    )
    _model1 = AbsorptionSpectrumSegment(
        kev_energy_interval=_energy_interval, absorption_calculator=_calculator
    )
    _single_interval: tuple[AbsorptionSpectrumSegment, ...] = (_model1,)
    _spectrum_calculator = MaterialAbsorptionSpectrum(intervals=_single_interval)
    assert _spectrum_calculator.absorption_coefficient_per_cm(
        energy_kev=20.0
    ) == pytest.approx(4.984205)


@pytest.mark.parametrize(
    "_in_band_kev",
    [
        13.1,
        24.91,
    ],
)
@pytest.mark.parametrize(
    "_lower,_upper", [(12.1, 15.9), (4.8, 19.67), (10.1, 20.01), (5, 18)]
)
def test_multi_band_material_absorption_spectrum_performs_in_band_calculation(
    _in_band_kev, _lower: float, _upper: float
) -> None:
    _energy_interval1: ClosedInterval = ClosedInterval(lower=_lower, upper=_upper)
    _calculator1: AbsorptionCalculator = SingleRollOffAbsorptionCalculator(
        material_factor_per_cm=6234.5, roll_off=-1.84
    )
    _model1 = AbsorptionSpectrumSegment(
        kev_energy_interval=_energy_interval1, absorption_calculator=_calculator1
    )
    _energy_interval2: ClosedInterval = ClosedInterval(lower=23.1, upper=38.6)
    _calculator2: AbsorptionCalculator = SingleRollOffAbsorptionCalculator(
        material_factor_per_cm=2824.5, roll_off=-2.84
    )
    _model2 = AbsorptionSpectrumSegment(
        kev_energy_interval=_energy_interval2, absorption_calculator=_calculator2
    )
    _multi_interval: tuple[AbsorptionSpectrumSegment, ...] = (
        _model1,
        _model2,
    )
    _spectrum_calculator = MaterialAbsorptionSpectrum(intervals=_multi_interval)

    assert (
        _spectrum_calculator.absorption_coefficient_per_cm(energy_kev=_in_band_kev)
        > 0.25
    )


# inauspicious path

INVALID_TRIAL_VALUES: Final[list[Any]] = [
    True,
    "",
    "a",
    "b00m!",
    [],
    KeyError(),
    None,
    math.sin,
    object(),
    False,
]


@pytest.mark.parametrize("_negative_energy", [-0.1, -12.3, -9739.43])
def test_photon_mass_attenuation_per_unit_length_errors_with_negative_energy(
    _negative_energy,
) -> None:
    _absorption_coefficient = 1.98e2
    _roll_off = -1.75
    with pytest.raises(ValidationError):
        photon_mass_attenuation_per_unit_length(
            energy_kev=_negative_energy,
            photon_absorption_factor_per_unit_length=_absorption_coefficient,
            energy_dependence_exponent=_roll_off,
        )


@pytest.mark.parametrize("_invalid_energy", INVALID_TRIAL_VALUES)
def test_photon_mass_attenuation_per_unit_length_errors_with_invalid_energy(
    _invalid_energy,
) -> None:
    _absorption_coefficient = 1.98e2
    _roll_off = -2.717
    with pytest.raises(ValidationError):
        photon_mass_attenuation_per_unit_length(
            energy_kev=_invalid_energy,
            photon_absorption_factor_per_unit_length=_absorption_coefficient,
            energy_dependence_exponent=_roll_off,
        )


@pytest.mark.parametrize("_invalid_absorption", INVALID_TRIAL_VALUES)
def test_photon_mass_attenuation_per_unit_length_errors_with_invalid_factor(
    _invalid_absorption,
) -> None:
    _energy_kev = 4.512
    _roll_off = -2.68
    with pytest.raises(ValidationError):
        photon_mass_attenuation_per_unit_length(
            energy_kev=_energy_kev,
            photon_absorption_factor_per_unit_length=_invalid_absorption,
            energy_dependence_exponent=_roll_off,
        )


@pytest.mark.parametrize("_invalid_roll_off", INVALID_TRIAL_VALUES)
def test_photon_mass_attenuation_per_unit_length_errors_with_invalid_exponent(
    _invalid_roll_off,
) -> None:
    _energy_kev = 13.819
    _absorption_coefficient = 2.148
    with pytest.raises(ValidationError):
        photon_mass_attenuation_per_unit_length(
            energy_kev=_energy_kev,
            photon_absorption_factor_per_unit_length=_absorption_coefficient,
            energy_dependence_exponent=_invalid_roll_off,
        )


def test_thickness_cm_required_to_attenuate_rejects_transparent_medium() -> None:
    _target_attenuation_bn = 2713.83
    transparent_medium = 0.0
    with pytest.raises(ValueError):
        thickness_cm_required_to_attenuate(
            target_attenuation_bn=_target_attenuation_bn,
            absorption_coefficient_per_cm=transparent_medium,
        )


@pytest.mark.parametrize(
    "_unphysical_alpha", [1.0e-15, 3.8e-12, 7.205e-9, -1.6, -0.002]
)
def test_thickness_cm_required_to_attenuate_rejects_unphysical_media(
    _unphysical_alpha,
) -> None:
    _target_attenuation = 750.0
    with pytest.raises(ValueError):
        thickness_cm_required_to_attenuate(
            target_attenuation_bn=_target_attenuation,
            absorption_coefficient_per_cm=_unphysical_alpha,
        )


@pytest.mark.parametrize("_invalid_target_attenuation", INVALID_TRIAL_VALUES)
def test_thickness_required_to_attenuate_raises_error_with_invalid_target_attenuation(
    _invalid_target_attenuation,
) -> None:
    _absorption_coefficient = 2.4
    with pytest.raises(ValidationError):
        thickness_cm_required_to_attenuate(
            target_attenuation_bn=_invalid_target_attenuation,
            absorption_coefficient_per_cm=_absorption_coefficient,
        )


@pytest.mark.parametrize("_invalid_absorption", INVALID_TRIAL_VALUES)
def test_thickness_required_to_attenuate_raises_error_with_invalid_absorption(
    _invalid_absorption,
) -> None:
    _target_attenuation = 1148.2
    with pytest.raises(ValidationError):
        thickness_cm_required_to_attenuate(
            target_attenuation_bn=_target_attenuation,
            absorption_coefficient_per_cm=_invalid_absorption,
        )


@pytest.mark.parametrize("_optical_gain", [-1, -5, -0.1])
def test_attenuation_at_depth_raises_error_with_ineligible_optical_gain(
    _optical_gain,
) -> None:
    _depth_cm = 0.152
    with pytest.raises(ValidationError):
        attenuation_at_depth_cm(
            depth_cm=_depth_cm, absorption_coefficient_per_cm=_optical_gain
        )


@pytest.mark.parametrize("_unphysical_depth", [-1, -5, -0.1])
def test_attenuation_at_depth_raises_error_for_unphysical_depths(
    _unphysical_depth,
) -> None:
    _absorption_coefficient = 1.1
    with pytest.raises(ValidationError):
        attenuation_at_depth_cm(
            depth_cm=_unphysical_depth,
            absorption_coefficient_per_cm=_absorption_coefficient,
        )


@pytest.mark.parametrize("_invalid_depth", INVALID_TRIAL_VALUES)
def test_attenuation_at_depth_raises_error_with_invalid_depth(_invalid_depth) -> None:
    _absorption_coefficient = 3.7
    with pytest.raises(ValidationError):
        attenuation_at_depth_cm(
            depth_cm=_invalid_depth,
            absorption_coefficient_per_cm=_absorption_coefficient,
        )


@pytest.mark.parametrize("_invalid_absorption", INVALID_TRIAL_VALUES)
def test_attenuation_at_depth_raises_error_with_invalid_attenuation(
    _invalid_absorption,
) -> None:
    _depth_cm = 0.425
    with pytest.raises(ValidationError):
        attenuation_at_depth_cm(
            depth_cm=_depth_cm, absorption_coefficient_per_cm=_invalid_absorption
        )


@pytest.mark.parametrize(
    "_out_of_band_kev",
    [
        (2.1, 96.3),
    ],
)
@pytest.mark.parametrize(
    "_lower,_upper", [(12.1, 21.9), (4.8, 49.67), (10.1, 20.01), (15, 31)]
)
def test_single_band_material_absorption_spectrum_rejects_out_of_band_calculation(
    _out_of_band_kev, _lower: float, _upper: float
) -> None:
    _energy_interval: ClosedInterval = ClosedInterval(lower=_lower, upper=_upper)
    _calculator: AbsorptionCalculator = SingleRollOffAbsorptionCalculator(
        material_factor_per_cm=1234.5, roll_off=-1.84
    )
    _model1 = AbsorptionSpectrumSegment(
        kev_energy_interval=_energy_interval, absorption_calculator=_calculator
    )
    _single_interval: tuple[AbsorptionSpectrumSegment, ...] = (_model1,)
    _spectrum_calculator = MaterialAbsorptionSpectrum(intervals=_single_interval)
    with pytest.raises(ValueError):
        _spectrum_calculator.absorption_coefficient_per_cm(energy_kev=_out_of_band_kev)


@pytest.mark.parametrize(
    "_out_of_band_kev",
    [
        (3.1, 22.83),
    ],
)
@pytest.mark.parametrize(
    "_lower,_upper", [(12.1, 15.9), (4.8, 19.67), (10.1, 20.01), (5, 11)]
)
def test_multi_band_material_absorption_spectrum_rejects_out_of_band_calculation(
    _out_of_band_kev, _lower: float, _upper: float
) -> None:
    _energy_interval1: ClosedInterval = ClosedInterval(lower=_lower, upper=_upper)
    _calculator1: AbsorptionCalculator = SingleRollOffAbsorptionCalculator(
        material_factor_per_cm=1234.5, roll_off=-1.84
    )
    _model1 = AbsorptionSpectrumSegment(
        kev_energy_interval=_energy_interval1, absorption_calculator=_calculator1
    )
    _energy_interval2: ClosedInterval = ClosedInterval(lower=23.1, upper=38.6)
    _calculator2: AbsorptionCalculator = SingleRollOffAbsorptionCalculator(
        material_factor_per_cm=234.5, roll_off=-2.84
    )
    _model2 = AbsorptionSpectrumSegment(
        kev_energy_interval=_energy_interval2, absorption_calculator=_calculator2
    )
    _multi_interval: tuple[AbsorptionSpectrumSegment, ...] = (
        _model2,
        _model1,
    )
    _spectrum_calculator = MaterialAbsorptionSpectrum(intervals=_multi_interval)
    with pytest.raises(ValueError):
        _spectrum_calculator.absorption_coefficient_per_cm(energy_kev=_out_of_band_kev)
