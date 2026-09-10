from functools import cached_property
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, model_validator

from dodal.common.general_maths.interval import ClosedInterval


class EnergyIntervalSpec(BaseModel):
    """JSON built sub-dict of one energy range, used in specifying material absorption spectra.

    Note:
        The range of energies is a closed interval, so inclusive of end values.

    Attributes:
        units: At present only 'keV' (or 'kiloelectronvolts') are supported.
        lower: The lower end of the energy interval (range) for specific absorption fit curve.
        upper: The upper end of the energy interval (range) for specific absorption fit curve.
    """

    units: Literal["keV", "kiloelectronvolts"]
    lower: StrictFloat = Field(gt=0.0)
    upper: StrictFloat = Field(gt=0.0)

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True, extra="forbid")

    @cached_property
    def as_interval(self) -> ClosedInterval:
        return ClosedInterval(lower=self.lower, upper=self.upper)

    @model_validator(mode="after")
    def _validate_attributes(self) -> "EnergyIntervalSpec":
        if self.lower < self.upper:
            return self
        _msg = f"Energy interval lower {self.lower} and upper {self.upper} bounds are in wrong order."
        raise ValueError(_msg)
