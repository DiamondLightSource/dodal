import math
from dataclasses import dataclass
from numbers import Real
from typing import Any

from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)


@dataclass(frozen=True)
class EnergySpecificAttenuation:
    attenuation_bn: float
    energy_kev: float

    def __post_init__(self) -> None:
        self._validate_arguments_by_type()
        self._validate_arguments_by_range()

    def _validate_arguments_by_type(self):
        for name, value, expectation in [
            ("attenuation_bn", self.attenuation_bn, "zero or positive"),
            ("energy_kev", self.energy_kev, "non-zero positive"),
        ]:
            if isinstance(value, bool) or not isinstance(value, Real):
                forbidden_type = type(value)
                raise TypeError(
                    f"Record field {name} should be a real {expectation} number, received instead {value} of impermissible type {forbidden_type}."
                )

    def _validate_arguments_by_range(self):
        if self.attenuation_bn < CANONICAL_NON_ABSORPTION:
            raise ValueError(
                f"Invalidly initialised with {self.attenuation_bn} Bn. Any attenuation in logarithmic Barnett Units cannot be less than {CANONICAL_NON_ABSORPTION}."
            )
        if not self.energy_kev > 0:
            raise ValueError(
                f"Invalidly initialised with {self.energy_kev} keV.  Photon energy must be a positive number."
            )

    def _are_energies_practically_identical(
        self, other: "EnergySpecificAttenuation"
    ) -> bool:
        return math.isclose(self.energy_kev, other.energy_kev, rel_tol=1.0e-7)

    def _create_residual_by_subtracting(
        self, other: "EnergySpecificAttenuation"
    ) -> "EnergySpecificAttenuation":
        reduced_bn = self.attenuation_bn - other.attenuation_bn
        return EnergySpecificAttenuation(
            attenuation_bn=reduced_bn, energy_kev=self.energy_kev
        )

    def __eq__(self, other: Any) -> bool:
        return (
            self.is_comparable_to(other) and self.attenuation_bn == other.attenuation_bn
        )

    def __gt__(self, other: Any) -> bool:
        return self.is_usefully_reducible_by(other)

    def _cover_incomparability_due_to_type_mismatch(
        self, other: Any, *, in_validation_mode: bool = False
    ) -> bool:
        if in_validation_mode:
            raise TypeError(
                f"Cannot compare instance of {type(self)} to argument of type {type(other)}."
            )
        else:
            return False

    def _cover_incomparability_due_to_energy_mismatch(
        self, other: "EnergySpecificAttenuation", *, in_validation_mode: bool = False
    ):
        if in_validation_mode:
            raise ValueError(
                f"Cannot perform meaningful attenuation comparison distinct energies {self.energy_kev} keV and {other.energy_kev} keV."
            )
        else:
            return False

    def is_comparable_to(self, other: Any, *, in_validation_mode: bool = False) -> bool:
        if isinstance(other, EnergySpecificAttenuation):
            return self._are_energies_practically_identical(
                other
            ) or self._cover_incomparability_due_to_energy_mismatch(
                other=other, in_validation_mode=in_validation_mode
            )
        else:
            return self._cover_incomparability_due_to_type_mismatch(
                other=other, in_validation_mode=in_validation_mode
            )

    def is_usefully_reducible_by(
        self, other: Any, *, in_validation_mode: bool = False
    ) -> bool:
        return (
            self.is_comparable_to(other, in_validation_mode=in_validation_mode)
            and not self.attenuation_bn < other.attenuation_bn
        )

    def reduce_attenuation_by(self, other: Any) -> "EnergySpecificAttenuation":
        if self.is_usefully_reducible_by(other, in_validation_mode=True):
            return self._create_residual_by_subtracting(other)
        else:
            raise ValueError(
                "Reduction would exceed attenuation of original demand - leading to an invalid negative residual"
            )
