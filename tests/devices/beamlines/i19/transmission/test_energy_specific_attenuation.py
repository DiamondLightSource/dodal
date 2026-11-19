import math
from typing import Any

import pytest

from dodal.devices.beamlines.i19.transmission.energy_specific_attenuation import (
    EnergySpecificAttenuation,
)


def test_that_energy_specific_attenuation_can_be_instantiated_from_its_elements() -> (
    None
):
    an_attenuation_bn = 1357.924
    an_energy_kev: float = 12.345
    assert (
        EnergySpecificAttenuation(
            attenuation_bn=an_attenuation_bn, energy_kev=an_energy_kev
        )
        is not None
    )


def test_that_energy_specific_attenuation_can_be_instantiated_with_integer_energy() -> (
    None
):
    an_attenuation_bn = 1357.924
    an_energy_kev = 14
    assert (
        EnergySpecificAttenuation(
            attenuation_bn=an_attenuation_bn, energy_kev=an_energy_kev
        )
        is not None
    )


def test_that_energy_specific_attenuation_can_be_instantiated_at_full_transmission() -> (
    None
):
    an_energy_kev: float = 19.678
    assert (
        EnergySpecificAttenuation.transparently_not_attenuating(
            energy_kev=an_energy_kev
        )
        is not None
    )


def test_that_energy_specific_attenuation_is_equal_to_itself() -> None:
    an_attenuation_bn = 1357.924
    an_energy_kev: float = 12.345
    a = EnergySpecificAttenuation(
        attenuation_bn=an_attenuation_bn, energy_kev=an_energy_kev
    )
    assert a == a


def test_that_energy_specific_attenuation_is_equal_to_another_with_same_values() -> (
    None
):
    an_attenuation_bn = 1357.924
    an_energy_kev: float = 12.345
    assert EnergySpecificAttenuation(
        attenuation_bn=an_attenuation_bn, energy_kev=an_energy_kev
    ) == EnergySpecificAttenuation(
        attenuation_bn=an_attenuation_bn, energy_kev=an_energy_kev
    )


def test_that_energy_specific_attenuation_is_unequal_where_attenuation_differs() -> (
    None
):
    an_attenuation_bn = 1357.924
    another_attenuation_bn = 168.2 + an_attenuation_bn
    an_energy_kev: float = 12.345
    assert EnergySpecificAttenuation(
        attenuation_bn=an_attenuation_bn, energy_kev=an_energy_kev
    ) != EnergySpecificAttenuation(
        attenuation_bn=another_attenuation_bn, energy_kev=an_energy_kev
    )


def test_that_energy_specific_attenuation_is_unequal_where_energy_differs() -> None:
    an_attenuation_bn = 1357.924
    an_energy_kev: float = 12.345
    a_different_energy_kev = an_energy_kev * 1.84
    assert EnergySpecificAttenuation(
        attenuation_bn=an_attenuation_bn, energy_kev=an_energy_kev
    ) != EnergySpecificAttenuation(
        attenuation_bn=an_attenuation_bn, energy_kev=a_different_energy_kev
    )


@pytest.mark.parametrize(
    "hypothetical_filter_attenuation_bn", [256.4, 812.8, 1278.339, 2459.043, 4051.2]
)
def test_one_energy_specific_attenuation_can_be_reduced_by_another_not_larger_at_same_energy(
    hypothetical_filter_attenuation_bn,
) -> None:
    example_energy_kev = 6.712
    demand_record = EnergySpecificAttenuation(
        attenuation_bn=4051.2, energy_kev=example_energy_kev
    )
    filter_contribution = EnergySpecificAttenuation(
        attenuation_bn=hypothetical_filter_attenuation_bn, energy_kev=example_energy_kev
    )
    residual = demand_record.reduce_attenuation_by(filter_contribution)
    assert isinstance(residual, EnergySpecificAttenuation)


@pytest.mark.parametrize(
    "hypothetical_filter_attenuation_bn", [1256.4, 1812.8, 2278.339, 3459.043, 5051.2]
)
def test_one_energy_specific_attenuation_can_report_when_another_is_larger_at_same_energy(
    hypothetical_filter_attenuation_bn,
) -> None:
    example_energy_kev = 18.56
    demand_record = EnergySpecificAttenuation(
        attenuation_bn=451.2, energy_kev=example_energy_kev
    )
    filter_contribution = EnergySpecificAttenuation(
        attenuation_bn=hypothetical_filter_attenuation_bn, energy_kev=example_energy_kev
    )
    assert filter_contribution > demand_record


@pytest.mark.parametrize(
    "hypothetical_energy_kev", [12.564, 18.128, 7.012, 22.7839, 23.453, 15.2]
)
def test_one_energy_specific_attenuation_cannot_be_compared_another_when_energies_differ(
    hypothetical_energy_kev,
) -> None:
    demand_record = EnergySpecificAttenuation(attenuation_bn=1451.2, energy_kev=5.432)
    filter_contribution = EnergySpecificAttenuation(
        attenuation_bn=687.2, energy_kev=hypothetical_energy_kev
    )
    assert not demand_record.is_usefully_reducible_by(filter_contribution)


# inauspicious path tests below


@pytest.mark.parametrize(
    "optical_gain_as_negative_attenuation", [-0.005, -2, -2060, -math.e, -713.5]
)
def test_energy_specific_attenuation_cannot_be_instantiated_with_neg_attenuation(
    optical_gain_as_negative_attenuation: float,
) -> None:
    an_energy_kev = 8.3113

    with pytest.raises(ValueError):
        EnergySpecificAttenuation(
            attenuation_bn=optical_gain_as_negative_attenuation,
            energy_kev=an_energy_kev,
        )


@pytest.mark.parametrize(
    "unphysical_kev",
    [
        0,
        -12,
        -17.3045,
        -math.pi,
    ],
)
def test_energy_specific_attenuation_cannot_be_instantiated_with_unphysical_energy(
    unphysical_kev: float,
) -> None:
    an_attenuation_bn = 256.408

    with pytest.raises(ValueError):
        EnergySpecificAttenuation(
            attenuation_bn=an_attenuation_bn, energy_kev=unphysical_kev
        )


NON_NUMERICALS: tuple[Any, ...] = (
    "1.5",
    "8",
    math.sin,
    True,
    False,
    KeyError(),
    object(),
    "Hello",
    {},
    [],
    (),
)


@pytest.mark.parametrize("non_numerical_attenuation", NON_NUMERICALS)
def test_that_error_raised_when_energy_specific_attenuation_fails_to_be_instantiated_with_non_numerical_attenuation(
    non_numerical_attenuation: Any,
) -> None:
    an_energy_kev = 24.8177

    with pytest.raises(TypeError):
        EnergySpecificAttenuation(
            attenuation_bn=non_numerical_attenuation, energy_kev=an_energy_kev
        )


@pytest.mark.parametrize("non_numerical_energy", NON_NUMERICALS)
def test_that_error_raised_when_energy_specific_attenuation_fails_to_be_instantiated_with_non_numerical_energy(
    non_numerical_energy: Any,
) -> None:
    an_attenuation_bn = 256.408

    with pytest.raises(TypeError):
        EnergySpecificAttenuation(
            attenuation_bn=an_attenuation_bn, energy_kev=non_numerical_energy
        )


@pytest.mark.parametrize(
    "hypothetical_filter_attenuation_bn", [1256.4, 1812.8, 2278.339, 3459.043, 5051.2]
)
def test_that_energy_specific_attenuation_cannot_be_validly_reduced_by_a_larger_attenuation_at_same_energy(
    hypothetical_filter_attenuation_bn,
) -> None:
    example_energy_kev = 18.56
    demand_record = EnergySpecificAttenuation(
        attenuation_bn=451.2, energy_kev=example_energy_kev
    )
    filter_contribution = EnergySpecificAttenuation(
        attenuation_bn=hypothetical_filter_attenuation_bn, energy_kev=example_energy_kev
    )
    assert demand_record < filter_contribution
    with pytest.raises(ValueError):
        # filter attenuation exceeds demand
        _overcooked_residual = demand_record.reduce_attenuation_by(filter_contribution)


@pytest.mark.parametrize(
    "hypothetical_energy_kev", [12.564, 18.128, 7.012, 22.7839, 23.453, 15.2]
)
def test_that_energy_specific_attenuation_raises_error_on_attempted_reduction_by_an_attenuation_at_distinct_energy(
    hypothetical_energy_kev,
) -> None:
    demand_record = EnergySpecificAttenuation(
        attenuation_bn=1451.2, energy_kev=hypothetical_energy_kev
    )

    with pytest.raises(ValueError):
        distinct_energy_kev = 18.56
        filter_contribution = EnergySpecificAttenuation(
            attenuation_bn=1023.6705, energy_kev=distinct_energy_kev
        )
        demand_record.reduce_attenuation_by(filter_contribution)


@pytest.mark.parametrize("other_type", NON_NUMERICALS)
def test_that_cannot_compare_to_instance_of_a_different_type(other_type: Any) -> None:
    assert not EnergySpecificAttenuation(
        attenuation_bn=567.789, energy_kev=12.345
    ).is_comparable_to(other_type)


@pytest.mark.parametrize("other_type", NON_NUMERICALS)
def test_that_error_raised_in_validation_mode_to_indicate_cannot_compare_to_instance_of_a_different_type(
    other_type: Any,
) -> None:
    example_energy_specific_attenuation = EnergySpecificAttenuation(
        attenuation_bn=567.789, energy_kev=12.345
    )
    with pytest.raises(TypeError):
        example_energy_specific_attenuation.is_comparable_to(
            other_type, in_validation_mode=True
        )
