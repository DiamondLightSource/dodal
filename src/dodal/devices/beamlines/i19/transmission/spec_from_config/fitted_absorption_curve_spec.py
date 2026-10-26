from typing import Final

from pydantic import BaseModel, ConfigDict, Field, StrictFloat

# A roll off exponent outside the -2.0 to -4.0 range is deemed unphysical
ROLL_OFF_UPPER_BOUND: Final[float] = -2.0
ROLL_OFF_LOWER_BOUND: Final[float] = -4.0


class FittedAbsorptionCurveSpec(BaseModel):
    """JSON built sub-dict of one absorption curve, used in specifying material absorption spectra.

    Note:
        One spectrum absorption curve covers a specific energy range where it is valid.
        One or more such curves make up one absorption spectrum.

    Attributes:
        photon_absorption:
            Material characteristic scaling constant which defines absorption curve.
        roll_off:
            Power-law exponent for variation with energy, usually something like -2.75 ∓ 0.24.
        residuals_polynomial_coeffs:
            Optional residuals correction, zeroth order parameter first.
    """

    photon_absorption: StrictFloat = Field(gt=0.0)
    roll_off: StrictFloat = Field(gt=ROLL_OFF_LOWER_BOUND, lt=ROLL_OFF_UPPER_BOUND)
    residuals_polynomial_coeffs: list[StrictFloat] = Field(default_factory=list)

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True, extra="forbid")
