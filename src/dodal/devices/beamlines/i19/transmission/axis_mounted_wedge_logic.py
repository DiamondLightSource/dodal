from collections.abc import Callable

from pydantic import (
    BaseModel,
    ConfigDict,
)

from dodal.common.general_maths.absorber_geometry import WedgeGeometry
from dodal.common.general_maths.interval import FloatInterval


class AxisMountedWedgeLogic(BaseModel):
    """Combines specified wedge tapered geometry with axial motor coordinate system parameters."""

    taper: WedgeGeometry
    out_position: float
    forbidden_zones: list[FloatInterval]
    active_region: FloatInterval

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    def closest_motor_position_mm_for_thickness_cm(
        self, *, thickness_cm: float
    ) -> float:
        # first solve for semi-infinite wedge (unbounded solution)
        unbounded_lateral_position = self.taper.motor_position_mm_for_thickness_cm(
            thickness_cm=thickness_cm
        )
        return (
            self._active_position_modulo_avoiding_bubbles(
                active_lateral_position_mm=unbounded_lateral_position
            )
            if unbounded_lateral_position in self.active_region
            else self._fallback_position_for_impractical_thickness(
                impractical_thickness_cm=thickness_cm
            )
        )

    def fulcrum_thickness(self) -> float:
        return self._less_attenuating_limit_of_position_interval(
            interval=self.active_region
        )

    def retracted_position(self) -> float:
        return self.out_position

    def thickness_cm_at_motor_position_mm(self, *, motor_position_mm: float) -> float:
        self._validate_motor_position_against_useable_active_wedge(
            motor_position_mm=motor_position_mm
        )
        return self.taper.thickness_cm_at_motor_position_mm(
            motor_position_mm=motor_position_mm
        )

    def threshold_position_mm(self) -> float:
        return self._less_attenuating_limit_of_position_interval(
            interval=self.active_region
        )

    def _active_position_modulo_avoiding_bubbles(
        self, *, active_lateral_position_mm: float
    ) -> float:
        relevant_exclusion = self._any_enclosing_forbidden_zone(
            potentially_enclosed_locus=active_lateral_position_mm
        )
        return (
            self._more_attenuating_limit_of_position_interval(
                interval=relevant_exclusion
            )
            if relevant_exclusion
            else active_lateral_position_mm
        )

    def _any_enclosing_forbidden_zone(
        self, *, potentially_enclosed_locus: float
    ) -> FloatInterval | None:
        return next(
            (fz for fz in self.forbidden_zones if potentially_enclosed_locus in fz),
            None,
        )

    def _depth_extremum_of_position_interval(
        self, *, position_interval: FloatInterval, extremum_func: Callable[..., float]
    ) -> float:
        """Common logic for asking which end of a range of wedge positions gives thinner/thicker depth.

        We directly ask the wedge rather than trying to reverse engineer it.
        Increasingly positive motor position is not necessarily increasing wedge thickness.

        Note: Motor axis position and sense in which the wedge taper is increasing,
        each have two potential directional polarities.
        There are therefore 4 possible scenarios which reduce to two equivalent pairs,
        with respect to direction for increasing thickness.
        """
        return extremum_func(
            position_interval.lower,
            position_interval.upper,
            key=self.taper.thickness_cm_at_motor_position_mm,
        )

    def _fallback_position_for_impractical_thickness(
        self, *, impractical_thickness_cm: float
    ) -> float:
        return (
            self.out_position
            if self.fulcrum_thickness() > impractical_thickness_cm
            else self._more_attenuating_limit_of_position_interval(
                interval=self.active_region
            )
        )

    def _less_attenuating_limit_of_position_interval(
        self, *, interval: FloatInterval
    ) -> float:
        return self._depth_extremum_of_position_interval(
            position_interval=interval, extremum_func=min
        )

    def _more_attenuating_limit_of_position_interval(
        self, *, interval: FloatInterval
    ) -> float:
        return self._depth_extremum_of_position_interval(
            position_interval=interval, extremum_func=max
        )

    def _validate_motor_position_against_useable_active_wedge(
        self, *, motor_position_mm: float
    ) -> None:
        self._verify_is_not_excluded_for_bubbles(motor_position_mm=motor_position_mm)
        self._verify_is_within_active_interval(motor_position_mm=motor_position_mm)

    def _verify_is_within_active_interval(self, *, motor_position_mm: float) -> None:
        if motor_position_mm not in self.active_region:
            raise ValueError(
                f"Hypothetical wedge motor position {motor_position_mm} outside active range."
            )

    def _verify_is_not_excluded_for_bubbles(self, *, motor_position_mm: float) -> None:
        if efz := self._any_enclosing_forbidden_zone(
            potentially_enclosed_locus=motor_position_mm
        ):
            raise ValueError(
                f"Hypothetical wedge motor position {motor_position_mm} lies within forbidden zone {efz}"
            )
