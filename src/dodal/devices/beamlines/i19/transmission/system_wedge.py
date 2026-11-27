from typing import Final

from pydantic.dataclasses import dataclass

from dodal.common.general_maths.absorbers import WedgeAbsorber
from dodal.common.general_maths.interval import (
    DirectedSegment,
)
from dodal.common.general_maths.material_absorption_maths import (
    IneligibleEnergyError,
)
from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
    PermittedKeyStr,
)
from dodal.devices.beamlines.i19.transmission.attenuation_system import (
    SupportsForecasting,
)
from dodal.devices.beamlines.i19.transmission.energy_specific_attenuation import (
    EnergySpecificAttenuation,
)


class InvalidLateralPositionError(ValueError):
    """Raised when a lateral position is neither within the active wedge range nor is retracted."""

    ...


class ForbiddenLateralPositionError(ValueError):
    """Raised when a lateral position is neither within the active wedge range nor is retracted."""

    ...


@dataclass(frozen=True)
class WedgePositionalBid:
    """A summary of the wedge's response to a system logic query - with the most suitable position the wedge can adopt.

    Attributes:
        demand: The energy specific system request for a specific attenuation, which combines,
            - Energy (of the x-rays) in keV.
            - Attenuation in logarithmic units.
        can_participate: Flags that the wedge is not too absorbing and not wavelength-inappropriate for the demand.
            - If True, this wedge is suitable for the stated demand ( per domain specific system requirements ).
            - If False, one or more aspects of the stated demand cannot be fulfilled.
        predicted_absorption: predicts the wedge absorption, if the proposed solution were to be implemented.
        proposed_motor_position: A wedge motor specific position solution corresponding either to,
            - the closest matching absorbing wedge position,
            - or to the wedge retraction position - where the demand goes unmet / unaddressed.
    """

    demand: EnergySpecificAttenuation
    is_eligible: (
        bool  # is able to contribute towards meeting the demand - without exceeding it
    )
    predicted_absorption_bn: float
    proposed_motor_position: AttenuatorMotorPositions


class ParametricWedgeLogic:
    """Handles conversion between wedge lateral motor position mm, thickness cm and bubble avoidance.

    Parameterises locations within the active wedge range from threshold to max,
    to a mapped fractional interval 0 to 1.
    Any bubble avoidance zones are similarly mapped to fractional positions in the active range.

    Attributes:
        retracted_motor_position_mm: Canonical position of the motor when the wedge is considered fully retracted from the x-ray beam.
        motor_tolerance_mm: magnitude of the smallest meaningful position change, given the readout precision and mechanical tolerances.
        viable_range_mm: Canonical interval from wedge threshold position to max thickness position near the end of the wedge.
        bubbles_mm: A collection of locations for bubbles to be avoided.
            - Note that the end ( rather than the start ) of the DirectedSegment for each bubble is the preferred bubble-adjacent alternative.
    """

    def __init__(
        self,
        *,
        retracted_motor_position_mm: float,
        motor_tolerance_mm: float = 1.0e-3,
        viable_range_mm: DirectedSegment,
        bubbles_mm: list[DirectedSegment],
    ):
        self.retracted_mm = retracted_motor_position_mm
        self._retraction_margin = DirectedSegment.create(
            start=self.retracted_mm - motor_tolerance_mm,
            end=self.retracted_mm + motor_tolerance_mm,
        )
        self.active_mm = viable_range_mm
        self._bubble_avoidance_zones_mm = tuple(bubbles_mm)
        self._matched_unit_interval = viable_range_mm.interval_cls(lower=0, upper=1)

    def _adjacent_boundary_of(
        self, *, bubble: DirectedSegment, move_to_thicker_end: bool = True
    ) -> float:
        return bubble.end if move_to_thicker_end else bubble.start

    def _find_any_coincident_bubble(
        self, *, position_mm: float
    ) -> DirectedSegment | None:
        for bubble in self._bubble_avoidance_zones_mm:
            if position_mm in bubble:
                return bubble
        return None

    def _is_consistent_with_retracted(self, *, position_mm: float) -> bool:
        return position_mm in self._retraction_margin

    def _lies_outside_active_range(self, *, position_mm: float) -> bool:
        return position_mm not in self.active_mm

    def _bubble_free_position_matching(
        self, *, parametric_position: float, work_around_bubbles: bool = True
    ) -> float:
        """Return the interpolated position, avoiding bubble bubbles when requested.

        Args:
            parametric_position:
                Fractional parameter which lies in the unit interval if within the active wedge.
            work_around_bubbles:
                - If True, coerce the interpolated position to a favoured bubble-adjacent position.
                - If False, raise an ForbiddenLateralPositionError if the position is associated with a bubble.

        Returns:
            The interpolated position if away from bubbles,
                or the favoured boundary of a bubble zone, when bubble avoidance is enabled.

        Raises:
            ForbiddenLateralPositionError:
                If any bubble is encountered and bubble avoidance is disabled.
        """
        raw_position_mm = self.active_mm.linear_interpolation_of_fraction(
            fractional_parameter=parametric_position
        )
        if (
            bubble := self._find_any_coincident_bubble(position_mm=raw_position_mm)
        ) is None:
            return raw_position_mm
        if work_around_bubbles:
            return self._adjacent_boundary_of(bubble=bubble)
        else:
            raise ForbiddenLateralPositionError(
                f"Parametric position {parametric_position:+.4f} "
                f"converted to {raw_position_mm:+.3f} mm "
                f"corresponds to a known wedge bubble."
            )

    def fractional_position_of(
        self,
        *,
        position_mm: float,
        strictly_unobstructed: bool = True,
        strictly_valid: bool = False,
    ) -> float | None:
        """Convert motor axis position into a parametric fractional value, based on the normalised active range of the wedge.

        Args:
            position_mm: A lateral position along the wedge motor axis scale, taking the definition of zero from the motor (rather than from wedge geometry).
            strictly_unobstructed: Governs behaviour with respect to any bubble in the wedge at the given position.
                - If True (default), raise ForbiddenLateralPositionError should the position happen to coincide with a bubble.
                - If False, ignore any bubble and thereby offer no guarantee that the output location is bubble free.
            strictly_valid: Governs behaviour with respect to active wedge range [threshold, max]
                - If True, raise InvalidLateralPositionError for any input position not in the [threshold to max] active range.
                - If False (default), perform the hypothetical conversion (of any real number position) irrespective of where it lies relative to the wedge.

        Returns:
            None, if the position given corresponds to the retracted motor position,
            otherwise any position within the active range is converted to a fraction within the [0,1] interval.
            Positions outside active and retracted will either raise an error or convert to a hypothetical fraction according to
            boolean flag argument settings (see Args)
        """
        if self._is_consistent_with_retracted(position_mm=position_mm):
            return None

        if strictly_valid and self._lies_outside_active_range(position_mm=position_mm):
            raise InvalidLateralPositionError(
                f"Lateral position {position_mm:+.3f} mm is not a permitted wedge position."
            )

        if (
            strictly_unobstructed
            and self._find_any_coincident_bubble(position_mm=position_mm) is not None
        ):
            raise ForbiddenLateralPositionError(
                f"Lateral position {position_mm:+.3f} mm lies within an identified bubble."
            )
        return self.active_mm.inverse_linear_interpolated_value(value=position_mm)

    def interpolated_lateral_position(
        self,
        *,
        parametric_fraction: float,
        work_around_bubbles: bool = True,
        strictly_valid: bool = False,
        coerce_to_wedge_maximum: bool = True,
    ) -> float:
        """Convert a parametric fraction [0,1] to a lateral motor position in mm.

        Args:
            parametric_fraction: Scaled to normalise against [0=threshold position, 1=wedge max]
            work_around_bubbles: Governs position adjustments when raw position lies in a bubble:
                - If True (default), coerce the position to the thicker of the bubble adjacent end points.
                - If False, make no bubble related adjustment,
                    but raise ForbiddenLateralPositionError if position lies in a bubble.
            strictly_valid: Pedantry setting for the parametric_fraction input argument.
                - If True, raise InvalidLateralPositionError if input fraction is outside the interval [0,1]
                - If False (default), convert the parametric fraction (any real number) to a motor axis equivalent position:
                    Asking for more attenuation than a wedge can deliver (i.e. parametric_fraction > 1)
                    is a canonically supported system use case for the aluminium wedge, hence False is the default.
            coerce_to_wedge_maximum: Governs position adjustments when raw position is beyond maximum (when strictly_valid is False):
                - If True (default), coerce the position back to the most attenuating position in the valid wedge range.
                - If False, make no such adjustment
                    (implicitly live with the position being "off the chunkier end" of the wedge).

        Returns:
            A position in mm along the lateral motor axis direction for the wedge,
                relative to motor scale zero.
                (In general neither the wedge tip, nor wedge threshold are at motor zero mm.)
        """
        # simplify if beyond maximum and coercion to max permitted
        if (
            parametric_fraction > self._matched_unit_interval.upper
            and coerce_to_wedge_maximum
        ):
            if not strictly_valid:
                return self.active_mm.end
            else:
                raise InvalidLateralPositionError(
                    f"Fractional position {parametric_fraction:+.4f} "
                    f"lies outside the active range of wedge lateral positions."
                )

        # reject invalid position if strict
        if strictly_valid and parametric_fraction not in self._matched_unit_interval:
            raise InvalidLateralPositionError(
                f"Fractional position {parametric_fraction:+.4f} "
                f"lies outside the active range of wedge lateral positions."
            )

        return self._bubble_free_position_matching(
            parametric_position=parametric_fraction,
            work_around_bubbles=work_around_bubbles,
        )


class _EnergySpecificAbsorptionProfile:
    """Snapshot of wedge capabilities at a specific energy, used to parameterise feasible absorption demands.

    Attributes:
        absorption_calculator: Provides wedge log-absorption values (at specific energy, lateral position).
        viable_range_mm: Wedge motor position range in use, directional towards thicker end.
        energy_kev: X-ray energy for which the profile has been calculated.
    """

    def __init__(
        self,
        *,
        absorption_calculator: WedgeAbsorber,
        viable_range_mm: DirectedSegment,
        energy_kev: float,
    ):
        _threshold_bn = absorption_calculator.calculate_absorption_bn(
            xray_energy_kev=energy_kev, motor_position_mm=viable_range_mm.start
        )
        _max_bn = absorption_calculator.calculate_absorption_bn(
            xray_energy_kev=energy_kev,
            motor_position_mm=viable_range_mm.end,
        )
        self.feasible_absorptions: Final[DirectedSegment] = DirectedSegment.create(
            start=_threshold_bn,
            end=_max_bn,
        )

    def absorption_to_raw_fractional_position(self, *, demand_bn: float) -> float:
        return self.feasible_absorptions.inverse_linear_interpolated_value(
            value=demand_bn
        )

    def fractional_position_to_absorption_bn(
        self, *, fractional_position: float
    ) -> float:
        return self.feasible_absorptions.linear_interpolation_of_fraction(
            fractional_parameter=fractional_position
        )


class SystemWedge(SupportsForecasting):
    @staticmethod
    def _is_below_wedge_threshold(parametric_fractional_position: float) -> bool:
        return parametric_fractional_position < 0

    def __init__(
        self,
        *,
        identifier: PermittedKeyStr,
        wedge_logic: ParametricWedgeLogic,
        absorption_calculator: WedgeAbsorber,
    ):
        self.axis_identifier = identifier
        self.absorption_calc = absorption_calculator
        self.parametric_tapered_logic = wedge_logic

    def _absorption_range(
        self, *, energy_kev: float
    ) -> _EnergySpecificAbsorptionProfile:
        return _EnergySpecificAbsorptionProfile(
            absorption_calculator=self.absorption_calc,
            viable_range_mm=self.parametric_tapered_logic.active_mm,
            energy_kev=energy_kev,
        )

    def _concrete_bid(
        self,
        *,
        demand: EnergySpecificAttenuation,
        parametric_fraction: float,
        coerce_to_maximum: bool = True,
        work_around_bubbles: bool = True,
    ) -> WedgePositionalBid:
        position_solution_mm: float = (
            self.parametric_tapered_logic.interpolated_lateral_position(
                parametric_fraction=parametric_fraction,
                work_around_bubbles=work_around_bubbles,
                coerce_to_wedge_maximum=coerce_to_maximum,
            )
        )
        proposed_motor_position = self._wrap_motor_position(
            position_mm=position_solution_mm
        )
        bid_prediction_bn = self._forecast_attenuation_at_position(
            energy_kev=demand.energy_kev, position_mm=position_solution_mm
        )
        return WedgePositionalBid(
            demand=demand,
            is_eligible=True,
            predicted_absorption_bn=bid_prediction_bn,
            proposed_motor_position=proposed_motor_position,
        )

    def _decline_demand_by_retracting_wedge(
        self, *, declined_demand: EnergySpecificAttenuation
    ) -> WedgePositionalBid:
        motor_retraction_in_wrapped_format = self._wrap_motor_position(
            position_mm=self.parametric_tapered_logic.retracted_mm
        )
        return WedgePositionalBid(
            demand=declined_demand,
            is_eligible=False,
            predicted_absorption_bn=CANONICAL_NON_ABSORPTION,
            proposed_motor_position=motor_retraction_in_wrapped_format,
        )

    def _forecast_attenuation_at_position(
        self, *, energy_kev: float, position_mm: float
    ) -> float:
        parametric_fraction = self.parametric_tapered_logic.fractional_position_of(
            position_mm=position_mm, strictly_unobstructed=True, strictly_valid=True
        )
        if parametric_fraction is None:
            return CANONICAL_NON_ABSORPTION
        else:
            absorption_range = self._absorption_range(energy_kev=energy_kev)
            return absorption_range.fractional_position_to_absorption_bn(
                fractional_position=parametric_fraction
            )

    def _is_eligible_for_energy_of(self, *, demand: EnergySpecificAttenuation) -> bool:
        return self.absorption_calc.is_eligible_for_energy(
            xray_energy_kev=demand.energy_kev
        )

    def _parametric_fractional_absorption_matching(
        self, *, demand: EnergySpecificAttenuation
    ) -> float | None:
        if not self._is_eligible_for_energy_of(demand=demand):
            return None
        raw_fraction = self._absorption_range(
            energy_kev=demand.energy_kev
        ).absorption_to_raw_fractional_position(demand_bn=demand.attenuation_bn)
        return None if self._is_below_wedge_threshold(raw_fraction) else raw_fraction

    def _unwrap_motor_position_mm(
        self, *, wrapped_positions: AttenuatorMotorPositions
    ) -> float:
        return wrapped_positions.continuous_positions[self.axis_identifier]

    def _wrap_motor_position(self, *, position_mm: float) -> AttenuatorMotorPositions:
        return AttenuatorMotorPositions(
            continuous_positions={self.axis_identifier: position_mm}
        )

    def forecast_attenuation(
        self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions
    ) -> float:
        if not self.absorption_calc.is_eligible_for_energy(xray_energy_kev=energy_kev):
            raise IneligibleEnergyError(
                "Cannot forecast attenuation at inappropriate "
                f"x-ray energy {energy_kev} keV."
            )
        extracted_position_mm = self._unwrap_motor_position_mm(
            wrapped_positions=attenuator_motor_positions
        )
        return self._forecast_attenuation_at_position(
            energy_kev=energy_kev, position_mm=extracted_position_mm
        )

    def propose_response_to_demand(
        self,
        *,
        demand: EnergySpecificAttenuation,
        work_around_bubbles: bool = True,
        coerce_to_maximum: bool = True,
    ) -> WedgePositionalBid:
        """Compute best wedge response to a specific absorption demand at a specific x-ray energy.

        Args:
            demand: The demand to be "owned" (fulfilled / attempted) or instead to be passed on to other subsystems.
            work_around_bubbles: Behavioural flag to govern bubble avoidance.
                - If True (default), bubbles to be avoided by coercing solution positions to bubble adjacent locations.
                - If False, raise errors if any requests would require positioning the x-ray beam onto a wedge bubble.
            coerce_to_maximum: ( overruled if strictly_valid arg is True )
                - If True (default), truncates any demand requiring the wedge to position itself beyond the max thickness.
                - If False, reports on hypothetical solutions even when these exceed the permitted wedge range.

        Returns:
            A summary of the wedge response to the system query, explaining what is possible within the given remit.
        """
        para_frac: float | None = self._parametric_fractional_absorption_matching(
            demand=demand
        )
        if para_frac is None:
            return self._decline_demand_by_retracting_wedge(declined_demand=demand)
        else:
            return self._concrete_bid(
                demand=demand,
                parametric_fraction=para_frac,
                coerce_to_maximum=coerce_to_maximum,
                work_around_bubbles=work_around_bubbles,
            )
