from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    model_validator,
)

from dodal.common.general_maths.interval import ClosedInterval
from dodal.devices.beamlines.i19.transmission.spec_from_config.name_validation import (
    AxisNameValidation,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.system_aspect_base_parser import (
    SystemAspectBaseParser,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.system_configuration import (
    SystemConfiguration,
)


class LateralMotorSpec(BaseModel):
    """The positions scale for an axial wedge motor (as specified by configuration, typically **JSON**).

    Notes:
        - The (potentially counterintuitive) class' attribute names match beamline scientists' "domain jargon".

        - Each lateral motor drives one absorber wedge sideways across the x-ray beam:
            - expected sideways motions are pure horizontal or pure vertical
                - but that's a detail, azimuthal orientation around the beam should not matter.
            - The position of the scale zero relative to the wedge location is hereby nailed down.
            - The wedge motor scale has
                - an **out** position
                - and then a range of "active" positions, ( where the mathematical assumption of a linear taper is reasonable ).

        - Although the units here will default to **mm** when unspecified (i.e. when omitted),
        the units setting is still likely to appear in the JSON, as a handy reminder to human readers of the configuration file.

    Attributes:
        units: At present only "mm" are supported.
        out: Motor position consistent with having fully retracted the wedge from the x-ray beam.
        threshold: Motor position for minimal absorption in the permitted active absorbing position range.
        max: Motor position for minimal absorption in the permitted active range.
        tolerance: Motor position accepted margin for readout error.
    """

    units: str = Field(default="mm")
    out: StrictFloat
    threshold: StrictFloat
    max: StrictFloat
    tolerance: StrictFloat = Field(default=5.0e-3)

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True, extra="forbid")

    @model_validator(mode="after")
    def validate_attributes(self) -> "LateralMotorSpec":
        # counter-intuitive naming, but depending on
        # motor scale orientation relative to wedge orientation
        # max (thickness) position could greater or smaller than threshold
        _lower = min(self.out, self.max)
        _upper = max(self.out, self.max)
        _interval = ClosedInterval(lower=_lower, upper=_upper)
        if self.threshold in _interval:
            return self
        msg: str = r"Inconsistent wedge geometry: Threshold not between max and out."
        raise ValueError(msg)


class LateralMotorsConfig(SystemAspectBaseParser[LateralMotorSpec]):
    """Maps from highest level configuration (JSON) dict to extract lateral motor specifications.

    Uses base class method **extract_specifications** and some pythonic type handling magic.

    See Also:
        Base of this parser class, namely **SystemAspectBaseParser**
    """

    def validate_key_name(self, *, key_name: str) -> None:
        AxisNameValidation.validate_axis_name(axis_name=key_name)

    @classmethod
    def extract_motors_specifications(
        cls,
        *,
        system_configuration: SystemConfiguration,
        motor_identifier: str,
    ) -> LateralMotorSpec:
        """Extracts wheel specification from configuration of the transmission system."""
        _motors: dict[str, LateralMotorSpec] = cls.get_aspect_specifications(
            system_configuration=system_configuration
        )
        return _motors[motor_identifier]
