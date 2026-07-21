from collections.abc import Callable
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    StrictFloat,
    StrictInt,
    field_validator,
    model_validator,
)

from .arithmetic_conversions import (
    convert_cm_to_mm,
    convert_microns_to_cm,
    convert_mm_to_cm,
    get_straight_line_y,
)

SupportedThicknessUnits = Annotated[
    Literal["cm", "mm", "um", "micron"], "Supported thickness units"
]


class FoilGeometry(BaseModel):
    """Represents flat shape of a specific foil absorber.

    Initialised with a foil thickness quantity in a supported thickness unit and,
    where necessary, converting this to a cm thickness.
    N.B. The missing "air" slot in a foil wheel is represented as a canonical / system "OUT" position,
    of the absorber - rather than as a zero thickness foil.

    Args:
        unit (str): one element from the set of supported choices - "cm", "mm", "um" or "micron"
        numerical_value (float): non-zero positive - physical thickness of the foil in the given units
    """

    # Class-level private dictionary - defined once only when the class is loaded
    _convertors: dict[str, Callable[[float], float]] = {
        "cm": lambda t: t,
        "mm": convert_mm_to_cm,
        "um": convert_microns_to_cm,
        "micron": convert_microns_to_cm,
    }

    unit: str
    numerical_value: Annotated[float, Field(gt=0.0)]
    _foil_thickness: float = PrivateAttr(default=0.0)

    @model_validator(mode="after")
    def _calculate_thickness(self) -> "FoilGeometry":
        # Look up directly from the conversion dictionary
        self._foil_thickness = self._convertors[self.unit](self.numerical_value)
        return self

    def get_thickness_cm(self) -> float:
        return self._foil_thickness


class WedgeGeometry(BaseModel):
    """Represents a semi infinite triangular prism wedge shape, growing out indefinitely from a tip.
    Initialised with cotangent of the wedge angle and offset between motor axis zero and wedge tip.
    N.B. absorber thickness are best worked out in cm (science), motor positions prefer mm (controls).
    Values used for inputs come from beamline scientist calibrations on real absorber.

    Args:
        tip_mm (float): unrestricted value, point on motor axis scale where modelled taper reaches zero thickness.
        taper_cotangent (float): taper angle cotangent, sign depends on motor direction convention, bounded to keep wedge angle thin.
    """

    tip_mm: StrictFloat | StrictInt
    taper_cotangent: StrictFloat | StrictInt
    _taper_gradient: float = PrivateAttr(default=0.0)

    @field_validator("taper_cotangent")
    @classmethod
    def validate_taper_is_thin(cls, value: float) -> float:
        bound = 5.0  # round number cotangent limit for thin wedge
        if -bound < value < bound:
            msg: str = f"taper_contangent must correspond to thin wedge, of magnitude {bound} or larger"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _calculate_gradient(self) -> Self:
        self._taper_gradient = 1.0 / self.taper_cotangent
        return self

    def motor_position_mm_for_thickness_cm(
        self, thickness_cm: Annotated[float, Field(ge=0.0)]
    ) -> float:
        """Hypothetical motor position at which the wedge thickness would take on the requested value.
        N.B. absorber thickness are best worked out in cm (science), motor positions prefer mm (controls).

        Args:
            thickness_cm: (float) non-negative float, zero permitted - the required target thickness in cm

        Returns:
            motor position in mm where a mathematical model wedge puts the target thickness in the x-ray beam
        """
        _line_offset = (
            self.tip_mm
        )  # Given that thickness (line x) is zero at this motor position (line y)
        _line_gradient = (
            self.taper_cotangent
        )  # small changes in thickness lead to large changes in position
        _x = convert_cm_to_mm(thickness_cm)  # do the line calculations in mm
        return get_straight_line_y(_line_offset, _line_gradient, _x)

    def thickness_cm_at_motor_position_mm(self, motor_position_mm: float) -> float:
        """Thickness of modelled wedge a given motor position in most useful units.
        N.B. The wedge geometry is not bounded by lateral position limits, but does reject,
        negative thickness,
        unlikely large taper angles (beyond about 11.31 degrees).

        Args:
            motor_position_mm: (float) unrestricted float, zero permitted - the required target thickness

        Returns:
            position in mm on the motor axis scale where a mathematical wedge would have the target thickness
        """
        _line_offset = (
            -self.tip_mm * self._taper_gradient
        )  # not immediately obvious - but after some algebra
        _line_gradient = self._taper_gradient
        _thickness_mm = get_straight_line_y(
            _line_offset, _line_gradient, motor_position_mm
        )
        return convert_mm_to_cm(_thickness_mm)
