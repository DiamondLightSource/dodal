from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    StrictFloat,
    model_validator,
)

from dodal.common.general_maths.interval import OpenInterval
from dodal.devices.beamlines.i19.transmission.spec_from_config.name_validation import (
    AxisNameValidation,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.system_aspect_base_parser import (
    SystemAspectBaseParser,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.system_configuration import (
    SystemConfiguration,
)


class BubbleVoidsListParser(RootModel[list[dict[str, Any]]]):
    """Parses and normalizes a list of bubble void sub-dictionaries before validation."""

    @model_validator(mode="before")
    @classmethod
    def convert_bubble_voids(cls, data: Any) -> Any:
        if isinstance(data, list):
            # Convert scientist friendly {"from": ..., "to": ...} dicts to interval friendly {"lower": ..., "upper": ...}
            return [
                {"lower": item["from"], "upper": item["to"]}
                if isinstance(item, dict) and "from" in item and "to" in item
                else item
                for item in data
            ]
        _msg = f"Expecting wedge bubble voids to be specified in a list format, rather than {type(data)}."
        raise ValueError(_msg)


class WedgeGeometrySpec(BaseModel):
    """The specification for a wedge shape (as specified by configuration, typically **JSON**).

    Attributes:
        taper_cotangent: slope of the wedge taper angle as defined by the cotangent of the small angle.
        tip: Virtual position which ties the mathematically modelled wedge's location in space to the motor axis scale.
        voids: optional listing of intervals where bubbles are to be avoided in the active range of wedge motor positions.

    See Also:
        LateralMotorSpec: for the motor axis positions specification details.
    """

    taper_cotangent: StrictFloat = Field(gt=5.0)
    tip: StrictFloat
    voids: list[OpenInterval] = Field(default_factory=list)

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True, extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def parse_voids(cls, data: Any) -> Any:
        if isinstance(data, dict) and "voids" in data:
            data["voids"] = BubbleVoidsListParser.model_validate(data["voids"]).root
        return data


class WedgeSpec(BaseModel):
    """The specification for a wedge motor (as specified by configuration, typically **JSON**).

    Notes:
        - Each absorber wedge has a motor to drive it sideways across the x-ray beam:
            - expected sideways motions are pure horizontal or pure vertical
                - but that's a detail, azimuthal orientation around the beam should not matter.
            - The wedge motor scale has
                - an **out** position
                - and then a range of "active" positions, ( where the mathematical assumption of a linear taper is reasonable ).

    Attributes:
        material: Name of the absorber material
            - as specified in the materials section of the transmission system configuration

    See Also:
        LateralMotorSpec
    """

    material: str
    geometry: WedgeGeometrySpec

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True, extra="forbid")


class WedgesConfig(SystemAspectBaseParser[WedgeSpec]):
    """Maps from highest level configuration (JSON) dict to extract wedge specifications.

    Uses base class method **extract_specifications** and some pythonic type handling magic.

    See Also:
        Base of this parser class, namely **SystemAspectBaseParser**
    """

    def validate_key_name(self, *, key_name: str) -> None:
        AxisNameValidation.validate_axis_name(axis_name=key_name)

    @classmethod
    def extract_wedge_specifications(
        cls,
        *,
        system_configuration: SystemConfiguration,
        wedge_identifier: str,
    ) -> WedgeSpec:
        """Extracts wedge specification from configuration of the transmission system."""
        _wedges: dict[str, WedgeSpec] = cls.get_aspect_specifications(
            system_configuration=system_configuration
        )
        return _wedges[wedge_identifier]
