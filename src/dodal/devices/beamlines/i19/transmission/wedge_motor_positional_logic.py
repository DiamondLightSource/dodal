
from collections.abc import Callable
from functools import cached_property
from typing import Final, Protocol

from dodal.common.general_maths.absorber_geometry import TaperedGeometryProvider
from dodal.common.general_maths.interval import FloatInterval
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
    PermittedKeyStr,
)


class WedgeInternalCoordinateLogic(Protocol):

    def is_forbidden_position(self, *, lateral_position_mm: float) -> float:
        ...

    def wedge_lateral_position_for_thickness(self, *, demand_thickness_cm: float) -> float: ...

    def wedge_lateral_position_for_maximum_thickness_(self) -> float:
        ...

    def wedge_lateral_position_on_threshold(self) -> float:
        ...


class ActivePositionsCalculator(WedgeInternalCoordinateLogic):

    def __init__(
        self,
        *,
        geometry: TaperedGeometryProvider,
        active_range: FloatInterval,
        forbidden_zones: list[FloatInterval]
    ):
        self.wedge_geometry: Final[TaperedGeometryProvider] = geometry
        self.usable_taper: Final[FloatInterval] = active_range
        self.bubbles: Final[list[FloatInterval]] = forbidden_zones

    def is_forbidden_position(self, *, lateral_position_mm: float) -> float:
        return any(lateral_position_mm in bubble for bubble in self.bubbles)

    def wedge_lateral_position_for_maximum_thickness_(self) -> float:
        return self._more_attenuating_end_of_interval(interval=self.usable_taper)

    def wedge_lateral_position_for_thickness(self, *, demand_thickness_cm: float) -> float:
        raw_pos = self.wedge_geometry.motor_position_mm_for_thickness_cm(
            thickness_cm=demand_thickness_cm
        )
        return self._avoiding_bubble(raw_position=raw_pos)

    def wedge_lateral_position_on_threshold(self) -> float:
        return self._less_attenuating_end_of_interval(interval=self.usable_taper)

    def _avoiding_bubble(self, *, raw_position: float) -> float:
        for bubble in self.bubbles:
            if raw_position in bubble:
                return self._more_attenuating_end_of_interval(interval=bubble)
        return raw_position  # no conflict with any bubble

    def _less_attenuating_end_of_interval(self, *, interval: FloatInterval) -> float:
        return self._selected_end_of_interval(extremis_function=min, interval=interval)

    def _more_attenuating_end_of_interval(self, *, interval: FloatInterval) -> float:
        return self._selected_end_of_interval(extremis_function=max, interval=interval)

    def _selected_end_of_interval(
        self,
        *,
        extremis_function: Callable[..., float],
        interval: FloatInterval
    ) -> float:
        ends: tuple[float, ...] = (interval.lower, interval.upper)  # positive motor and taper increase direction could be parallel or anti-parallel
        return extremis_function(
            ends,
            key=lambda end_pos: self.wedge_geometry.thickness_cm_at_motor_position_mm(
                motor_position_mm=end_pos
            )
        )

class WedgeMotorPositionalLogic(Protocol):

    def extract_lateral_wedge_position_lateral_wedge_position(self, *, attenuator_motor_positions: AttenuatorMotorPositions) -> float:
        ...

    def get_wedge_coordinates(self) -> WedgeInternalCoordinateLogic:
        ...

    def identify_wedge_motor_axis(self) -> PermittedKeyStr:
        ...

    def retracted_motor_positions(self) -> AttenuatorMotorPositions:
        ...

    def would_wedge_be_retracted_at(self, *, attenuator_motor_positions: AttenuatorMotorPositions) -> bool:
        ...

class MotorPositionsCalculator(WedgeMotorPositionalLogic):
    def __init__(
        self,
        *,
        retracted_position_with_margins_mm: FloatInterval,
        motor_axis_identifier: PermittedKeyStr,
        internal_geometry_logic: WedgeInternalCoordinateLogic,
    ):
        self._axis_identifier: Final[PermittedKeyStr] = motor_axis_identifier
        self._retracted_margin: Final[FloatInterval] = retracted_position_with_margins_mm
        self._shape_logic: Final[WedgeInternalCoordinateLogic] = internal_geometry_logic

    @cached_property
    def _retracted_position(self) -> AttenuatorMotorPositions:
        centre:float = 0.5 * (self._retracted_margin.lower + self._retracted_margin.upper)
        _wrapped_centre = { self. _axis_identifier: centre }
        return AttenuatorMotorPositions(continuous_positions=_wrapped_centre)

    def extract_lateral_wedge_position(self, *, attenuator_motor_positions: AttenuatorMotorPositions) -> float:
        return attenuator_motor_positions.continuous_positions[self._axis_identifier]

    def get_wedge_coordinates(self) -> WedgeInternalCoordinateLogic:
        return self._shape_logic

    def identify_wedge_motor_axis(self) -> PermittedKeyStr:
        return self._axis_identifier

    def retracted_motor_positions(self) -> AttenuatorMotorPositions:
        return self._retracted_position

    def would_wedge_be_retracted_at(self, *, attenuator_motor_positions: AttenuatorMotorPositions) -> bool:
        lateral_position = self.extract_lateral_wedge_position(attenuator_motor_positions=attenuator_motor_positions)
        return lateral_position in self._retracted_margin
