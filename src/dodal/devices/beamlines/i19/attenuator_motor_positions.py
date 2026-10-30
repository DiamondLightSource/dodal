import math
from functools import cached_property
from typing import Annotated, Any, Final, Self, final

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    model_validator,
)
from pydantic.types import StringConstraints

PermittedKeyStr = Annotated[
    str, StringConstraints(pattern=r"^[_A-Za-z][A-Za-z0-9-_]*$")
]

UndefinedMotorTolerances: Final[dict[PermittedKeyStr, float]] = {}
FallbackMotorTolerance: Final[float] = 1.0e-4  # in mm i.e. 100 nm

@final
class AttenuatorMotorPositions(BaseModel):
    """Motor positions for attentuators in the attenuation system, be they indices on a discrete steps motor or continuous positions on an axis, or axes.

    This is a validated dict which pairs off naming "tags" for each motor (e.g. "x" for a lateral x-axis motor or "w" for a filter wheel),
    with the corresponding int or float motor position ( or position demand / request ) as appropriate.

    Attributes:
        continuous_positions: dict contributions pairing names of motors against the discrete motor position (likely to be in mm)/
        discrete_indices: dict contributions pairing names of index stepping positioners against the discrete position index (e.g. for a filter wheel).

    Examples:
        ( Given that i19 mounted a resin wedge on their x-axis motor,
            an aluminium wedge on their y-axis motor and their first filter wheel we will name "w" ... )

        Request for motor changes:
            {"x": 20.4} and {"w":3} might indicate a request to move x-axis to 20.4 mm and the wheel round to slot 3.

        Reporting of system motor positions (on say i19, where wheel index 1 is reserved for an EMPTY slot):
        {"x": 28.62, "y": 5.0} and {"w": 1} might indicate the resin wedge is at 28.62 mm, aluminium wedge is OUT, filter wheel at EMPTY (OUT)."
    """

    model_config = ConfigDict(frozen=True)

    continuous_positions: dict[PermittedKeyStr, StrictFloat | StrictInt] = Field(
        default_factory=dict, kw_only=True
    )
    discrete_indices: dict[PermittedKeyStr, Annotated[StrictInt, Field(gt=0)]] = Field(
        default_factory=dict, kw_only=True
    )

    @staticmethod
    def _confirm_no_keys_clash(
        a: dict[PermittedKeyStr, Any], b: dict[PermittedKeyStr, Any]
    ) -> None:
        common_keys = set(a).intersection(b)
        common_key_count = len(common_keys)
        if common_key_count > 0:
            ks: str = "key" if common_key_count == 1 else "keys"
            raise ValueError(
                f"Common {ks} found in motor positions: {common_keys}"
            )

    @model_validator(mode="after")
    def no_keys_clash(self) -> Self:
        self._confirm_no_keys_clash(self.continuous_positions, self.discrete_indices)
        return self

    def _confirm_merge_compatibility(self, other: object) -> None:
        if isinstance(other, AttenuatorMotorPositions):
            self._confirm_no_keys_clash(self.discrete_indices, other.discrete_indices)
            self._confirm_no_keys_clash(
                self.continuous_positions, other.continuous_positions
            )

    @cached_property
    def validated_and_complete(
        self,
    ) -> dict[PermittedKeyStr, StrictInt | StrictFloat]:
        """Lazily evaluate the merged dict, post validation and cache for future use.

        Returns:
            The validated union of both discrete motor index and continuous motor position contributions.
        """
        return self.continuous_positions | self.discrete_indices

    def is_practically_equal_to(
        self,
        *,
        other: Any,
        fallback_motor_tolerance: float = 1.0e-4,
        motor_tolerances: dict[PermittedKeyStr, float]=UndefinedMotorTolerances,
    ) -> bool:
        return (
            isinstance(other, AttenuatorMotorPositions)
            and self._shares_common_keys_and_all_common_values_match_within_tolerance(
                other=other,
                fallback_motor_tolerance=fallback_motor_tolerance,
                motor_tolerances=motor_tolerances
            )
        )

    def is_empty(self) -> bool:
        return not self.validated_and_complete

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, AttenuatorMotorPositions)
            and self.validated_and_complete == other.validated_and_complete
        )

    def __or__(self, other: object) -> "AttenuatorMotorPositions":
        if not isinstance(other, AttenuatorMotorPositions):
            return self
        elif self.is_empty():
            return other
        else:
            self._confirm_merge_compatibility(other)
            return AttenuatorMotorPositions(
                continuous_positions=self.continuous_positions
                | other.continuous_positions,
                discrete_indices=self.discrete_indices | other.discrete_indices,
            )

    def __repr__(self) -> str:
        return f"{self.validated_and_complete}"

    def _shares_common_keys_and_all_common_values_match_within_tolerance(
        self,
        *,
        other: "AttenuatorMotorPositions",
        fallback_motor_tolerance: float,
        motor_tolerances: dict[PermittedKeyStr, float],
    ) -> bool:
        common_wheels = set(self.discrete_indices).intersection(other.discrete_indices)
        for wheel_name in common_wheels:
            consistent_indices_on_same_wheel = bool(
                self.discrete_indices[wheel_name]
                == other.discrete_indices[wheel_name]
            )
            if not consistent_indices_on_same_wheel:
                return False
        at_least_one_wheel_in_common_and_all_wheel_indices_matched = bool(common_wheels)

        common_wedges = set(self.continuous_positions).intersection(other.continuous_positions)
        for wedge_name in common_wedges:
            motor_margin: float = (
                motor_tolerances[wedge_name]
                if wedge_name in motor_tolerances
                else fallback_motor_tolerance
            )
            consistent_positions_on_same_wedge = math.isclose(
                self.continuous_positions[wedge_name],
                other.continuous_positions[wedge_name],
                abs_tol=motor_margin,
            )
            if not consistent_positions_on_same_wedge:
                return False
        at_least_one_wedge_in_common_and_all_wedge_positions_match_within_tolerance = bool(common_wedges)

        return (
            at_least_one_wedge_in_common_and_all_wedge_positions_match_within_tolerance
            or
            at_least_one_wheel_in_common_and_all_wheel_indices_matched
        )
