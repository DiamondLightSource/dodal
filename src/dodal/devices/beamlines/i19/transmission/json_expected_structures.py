from pydantic import BaseModel, Field, StrictFloat, model_validator

# Exact match of expected JSON structures:
# Each class has attributes which match the exact key names in JSON
# used by scientists to specificy the transmission system parameters.


class EnergyIntervalJsonValidation(BaseModel):
    """Sub-dict of one energy range (ClosedInterval).

    Attributes:
        units: At present only keV are supported.
        lower: The lower end of the energy interval (range) for specific absorption fit curve.
        upper: The upper end of the energy interval (range) for specific absorption fit curve.
    """

    units: str = Field(..., pattern=r"^(keV|kiloelectronvolts)$")
    lower: StrictFloat
    upper: StrictFloat

    @model_validator(mode="after")
    def validate_attributes(self) -> "EnergyIntervalJsonValidation":
        if 0.0 < self.lower < self.upper:
            return self
        _msg = (
            f"Energy interval lower {self.lower} and upper {self.upper} bounds are in wrong order."
            if self.lower > 0.0
            else f"Energy bound use {self.lower} to define lower end of x-ray energy interval, must be greater than zero."
        )
        raise ValueError(_msg)


class AbsorptionCurveFitParametersJsonValidation(BaseModel):
    """Sub-dict of one spectrum absorption curve (over an energy range of validity).

    Attributes:
        photon_absorption: Material characteristic scaling constant which defines absorption curve.
        roll_off: Absorption variation as a function of energy, typically ranging from -2.5 to -3
        residuals_polynomial_coeffs: optional residuals correction, zeroth order parameter first
    """

    photon_absorption: StrictFloat
    roll_off: StrictFloat
    residuals_polynomial_coeffs: list[StrictFloat] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_attributes(self) -> "AbsorptionCurveFitParametersJsonValidation":
        if self.photon_absorption > 0.0 and self.roll_off < 2.0:
            return self
        if not self.photon_absorption > 0:
            raise ValueError(
                f"Photon absorption constant {self.photon_absorption} is invalid."
            )
        raise ValueError(
            f"Absorption roll off {self.roll_off} does not match the physically expected -2.0 or below."
        )
