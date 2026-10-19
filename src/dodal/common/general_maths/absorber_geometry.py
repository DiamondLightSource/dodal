from collections.abc import Callable
from functools import cached_property
from typing import Annotated, Literal, Protocol, runtime_checkable

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    StrictFloat,
    field_validator,
    model_validator,
)

from dodal.common.general_maths.arithmetic_conversions import (
    convert_cm_to_mm,
    convert_microns_to_cm,
    convert_mm_to_cm,
    get_straight_line_y,
)
from dodal.common.general_maths.interval import (
    FloatInterval,
    OpenInterval,
)

SupportedThicknessUnits = Annotated[
    Literal["cm", "mm", "um", "micron"], "Supported thickness units"
]


@runtime_checkable
class ThicknessProvider(Protocol):
    """Provider API which the standard FoilGeometry implements.

    Used here to make FoilAbsorber easier to test.
    """

    def get_thickness_cm(self) -> float: ...


@runtime_checkable
class TaperedGeometryProvider(Protocol):
    """Provider API which the standard WedgeGeometry implements.

    Used here to make WedgeAbsorber easier to test.
    """

    def thickness_cm_at_motor_position_mm(
        self, *, motor_position_mm: StrictFloat
    ) -> float: ...


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
    numerical_value: Annotated[StrictFloat, Field(gt=0.0)]
    _foil_thickness: float = PrivateAttr(default=0.0)

    @model_validator(mode="after")
    def _pre_calculate_thickness(self) -> "FoilGeometry":
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
        tip_mm (StrictFloat): unrestricted value, point on motor axis scale where modelled taper reaches zero thickness.
        taper_cotangent (StrictFloat): taper angle cotangent, sign depends on motor direction convention, bounded to keep wedge angle thin.
    """

    tip_mm: StrictFloat
    taper_cotangent: StrictFloat

    model_config = ConfigDict(frozen=True)

    @field_validator("taper_cotangent")
    @classmethod
    def validate_taper_is_thin(cls, value: float, _magnitude=5) -> float:
        _invalid_taper_range: FloatInterval = OpenInterval(
            lower=-_magnitude, upper=_magnitude
        )  # round number cotangent limit for thin wedge
        if value in _invalid_taper_range:
            _msg: str = f"taper_contangent must correspond to thin wedge, of magnitude {_magnitude} or larger"
            raise ValueError(_msg)
        return value

    @cached_property
    def _taper_gradient(self) -> float:
        return 1.0 / self.taper_cotangent

    def motor_position_mm_for_thickness_cm(
        self, *, thickness_cm: Annotated[StrictFloat, Field(ge=0.0)]
    ) -> float:
        """Hypothetical motor position at which the wedge thickness would take on the requested value.
        N.B. absorber thickness are best worked out in cm (science), motor positions prefer mm (controls).

        Args:
            thickness_cm: (StrictFloat) non-negative float, zero permitted - the required target thickness in cm

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

    def thickness_cm_at_motor_position_mm(
        self, *, motor_position_mm: StrictFloat
    ) -> float:
        """Thickness of modelled wedge a given motor position in most useful units.
        N.B. The wedge geometry is not bounded by lateral position limits, but does reject,
        negative thickness,
        unlikely large taper angles (beyond about 11.31 degrees).

        Args:
            motor_position_mm: (StrictFloat) unrestricted float, zero permitted - the required target thickness

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
