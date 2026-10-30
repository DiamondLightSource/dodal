from collections.abc import Callable
from functools import cached_property
from typing import Final, Protocol

from dodal.common.general_maths.absorber_geometry import TaperedGeometryProvider
from dodal.common.general_maths.arithmetic_conversions import (
    parametric_fraction,
    parametrised_value,
)
from dodal.common.general_maths.interval import FloatInterval
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
    PermittedKeyStr,
)


class InvalidWedgeMotorPositionError(ValueError): ...


class ParametricWedgeCoordinates(Protocol):
    def is_forbidden_position(self, *, parametric_lateral_position: float) -> float: ...

    def parametric_lateral_position(
        self, *, parametric_fraction: float, actively_escape_from_bubble: bool = True
    ) -> float: ...


class ParametricWedgePositionsCalculator(ParametricWedgeCoordinates):
    def __init__(
        self,
        *,
        geometry: TaperedGeometryProvider,
        active_range_mm: FloatInterval,
        forbidden_zones_mm: list[FloatInterval],
    ):
        self.wedge_geometry: Final[TaperedGeometryProvider] = geometry
        self.usable_taper_mm: Final[FloatInterval] = active_range_mm
        parametric_fraction()
        self.parametric_bubbles: Final[list[FloatInterval]] = parametric_forbidden_zones
        self._validate_on_construction()



    def is_forbidden_position(self, *, lateral_position_mm: float) -> bool:
        return any(lateral_position_mm in bubble for bubble in self.bubbles)

    def parametric_lateral_position(
        self, *, parametric_fraction: float, actively_escape_from_bubble: bool = True
    ) -> float:
        raw_lateral_mm = parametrised_value(
            interval=self.usable_taper, parametric_fraction=parametric_fraction
        )
        if not actively_escape_from_bubble:
            return raw_lateral_mm
        else:
            return self._climb_uphill_out_of_any_bubble(raw_position=raw_lateral_mm)

    def wedge_lateral_position_for_maximum_thickness(self) -> float:
        return self._more_attenuating_end_of_interval(interval=self.usable_taper)

    def wedge_lateral_position_for_thickness(
        self, *, demand_thickness_cm: float
    ) -> float:
        raw_pos = self.wedge_geometry.motor_position_mm_for_thickness_cm(
            thickness_cm=demand_thickness_cm
        )
        return self._climb_uphill_out_of_any_bubble(raw_position=raw_pos)

    def wedge_lateral_position_on_threshold(self) -> float:
        return self._less_attenuating_end_of_interval(interval=self.usable_taper)

    def wedge_thickness_cm_at_lateral_position_mm(
        self, *, lateral_position_mm: float, actively_escaping_from_bubble: bool = True
    ) -> float:
        if lateral_position_mm not in self.usable_taper:
            raise InvalidWedgeMotorPositionError(
                f"Lateral motor position {lateral_position_mm} mm, would not place the usable portion of the wedge in the x-ray beam."
            )
        active_position_mm = (
            self._climb_uphill_out_of_any_bubble(raw_position=lateral_position_mm)
            if actively_escaping_from_bubble
            else lateral_position_mm
        )
        if self.is_forbidden_position(lateral_position_mm=active_position_mm):
            raise InvalidWedgeMotorPositionError(
                f"Lateral motor position {lateral_position_mm} mm, lies within forbidden bubble."
            )
        return self.wedge_geometry.thickness_cm_at_motor_position_mm(
            motor_position_mm=active_position_mm
        )

    def _climb_uphill_out_of_any_bubble(self, *, raw_position: float) -> float:
        for bubble in self.bubbles:
            if raw_position in bubble:
                return self._more_attenuating_end_of_interval(interval=bubble)
        return raw_position  # no conflict with any bubble

    def _less_attenuating_end_of_interval(self, *, interval: FloatInterval) -> float:
        return self._selected_end_of_interval(extremis_function=min, interval=interval)

    def _more_attenuating_end_of_interval(self, *, interval: FloatInterval) -> float:
        return self._selected_end_of_interval(extremis_function=max, interval=interval)

    def _selected_end_of_interval(
        self, *, extremis_function: Callable[..., float], interval: FloatInterval
    ) -> float:
        ends: tuple[float, ...] = (
            interval.lower,
            interval.upper,
        )  # positive motor and taper increase direction could be parallel or anti-parallel
        return extremis_function(
            ends,
            key=lambda end_pos: self.wedge_geometry.thickness_cm_at_motor_position_mm(
                motor_position_mm=end_pos
            ),
        )


class WedgeMotorPositionalLogic(Protocol):
    def get_wedge_coordinates(self) -> ParametricWedgeCoordinates: ...

    def identify_wedge_motor_axis(self) -> PermittedKeyStr: ...

    def retracted_motor_positions(self) -> AttenuatorMotorPositions: ...

    def would_wedge_be_retracted_at(
        self, *, attenuator_motor_positions: AttenuatorMotorPositions
    ) -> bool: ...

    def wrap_raw_motor_position_mm(
        self, *, raw_position_mm: float
    ) -> AttenuatorMotorPositions: ...


class LateralPositionsLogic(WedgeMotorPositionalLogic):
    def __init__(
        self,
        *,
        retracted_position_with_margins_mm: FloatInterval,
        motor_axis_identifier: PermittedKeyStr,
        internal_geometric_calculator: ParametricWedgeCoordinates,
    ):
        self._axis_identifier: Final[PermittedKeyStr] = motor_axis_identifier
        self._is_retracted_to_within_motor_tolerance = lambda pos: (
            pos in retracted_position_with_margins_mm
        )
        self._nominal_retracted_position = parametrised_value(
            interval=retracted_position_with_margins_mm, parametric_fraction=0.5
        )
        self._shape_logic: Final[ParametricWedgeCoordinates] = (
            internal_geometric_calculator
        )

    @cached_property
    def _retracted_position(self) -> AttenuatorMotorPositions:
        return self.wrap_raw_motor_position_mm(
            raw_position_mm=self._nominal_retracted_position
        )

    def extract_lateral_wedge_position(
        self, *, attenuator_motor_positions: AttenuatorMotorPositions
    ) -> float:
        return attenuator_motor_positions.continuous_positions[self._axis_identifier]

    def get_wedge_coordinates(self) -> ParametricWedgeCoordinates:
        return self._shape_logic

    def identify_wedge_motor_axis(self) -> PermittedKeyStr:
        return self._axis_identifier

    def retracted_motor_positions(self) -> AttenuatorMotorPositions:
        return self._retracted_position

    def would_wedge_be_retracted_at(
        self, *, attenuator_motor_positions: AttenuatorMotorPositions
    ) -> bool:
        lateral_position = self.extract_lateral_wedge_position(
            attenuator_motor_positions=attenuator_motor_positions
        )
        return self._is_retracted_to_within_motor_tolerance(lateral_position)

    def wrap_raw_motor_position_mm(
        self, *, raw_position_mm: float
    ) -> AttenuatorMotorPositions:
        return AttenuatorMotorPositions(
            continuous_positions={self._axis_identifier: raw_position_mm}
        )
