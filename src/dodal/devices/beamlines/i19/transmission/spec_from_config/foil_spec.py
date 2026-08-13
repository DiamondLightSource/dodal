from pydantic import (
    BaseModel,
    ConfigDict,
    StrictFloat,
)


class FoilThicknessSpec(BaseModel):
    """The specification for a flat foil thickness (as specified by configuration, typically **JSON**).

    Attributes:
        units: The length unit used to specify the foil thickness.
        value: The foil thickness in the specified unit.
    """

    units: str
    value: StrictFloat

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True, extra="forbid")


class AbsorberSpec(BaseModel):
    """The specification for a FixedDepth absorber (as specified by configuration, typically **JSON**).

    Attributes:
        material: The name of the absorber material, as present the in the materials section of the configuration.
        thickness: ThicknessProvider geometry of the flat foil absorber.
    """

    material: str
    thickness: FoilThicknessSpec

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True, extra="forbid")


class FoilSpec(BaseModel):
    """The specification for a filter slot in a wheel.

    Attributes:
        absorber: Absorbing filter configuration for a given slot.
    """

    absorber: AbsorberSpec

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True, extra="forbid")
