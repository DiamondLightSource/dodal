from typing import Final

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, model_validator

from dodal.common.general_maths.interval import ClosedInterval, FloatInterval

PHYSICAL_ROLL_OFF: Final[FloatInterval] = ClosedInterval(lower=-4.0, upper=-2.0)


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

    photon_absorption: StrictFloat
    roll_off: StrictFloat
    residuals_polynomial_coeffs: list[StrictFloat] = Field(default_factory=list)

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True, extra="forbid")

    @model_validator(mode="after")
    def validate_attributes(self) -> "FittedAbsorptionCurveSpec":
        if self.photon_absorption > 0.0 and self.roll_off in PHYSICAL_ROLL_OFF:
            return self
        if not self.photon_absorption > 0:
            raise ValueError(
                f"Photon absorption constant {self.photon_absorption} is invalid."
            )
        _msg = (
            f"Absorption roll off {self.roll_off} does not seem likely on physics grounds."
            if self.roll_off < 0
            else "Absorption roll off is a negative exponent typically close to -3.0 ∓ 1"
        )
        raise ValueError(_msg)
