
from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from typing import Final, Protocol, TypeVar

from dodal.common.general_maths.absorbers import VariableDepth
from dodal.common.general_maths.arithmetic_conversions import (
    parametric_fraction,
    parametrised_value,
)
from dodal.common.general_maths.interval import ClosedInterval
from dodal.common.general_maths.material_absorption_maths import IneligibleEnergyError
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.energy_specific_attenuation import (
    EnergySpecificAttenuation,
)
from dodal.devices.beamlines.i19.transmission.wedge_motor_positional_logic import (
    WedgeMotorPositionalLogic,
)
from dodal.log import LOGGER

P = TypeVar("P", bound=Callable[..., EnergySpecificAttenuation])

class SupportsForecasting(Protocol):

    def is_an_energy_appropriate_state(self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions) -> bool: ...

    def is_a_fully_retracted_state(self, *, attenuator_motor_positions: AttenuatorMotorPositions) -> bool: ...

    def predict_attenuation_bn(self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions) -> EnergySpecificAttenuation: ...


def transparent_when_retracted(attenuation_predictor_func: P) -> P:
    """Decorator to short-circuit detailed attenuation calculations when absorbers are retracted from the x-ray beam.

    When the motor positions indicate that the relevant absorber (or absorbers) are (all) retracted,
    this short cut will return the transparent pairing of the demand's energy with the canonical transparent attenuation.

    Note:
        If any absorber is not retracted, the more detailed calculations are attempted:
        The absorber (absorption calculation model) eligibility at the demand energy is checked and if appropriate the attenuation calculated;
        if instead the absorber is not eligible at the demand energy an error is raised
    """
    @wraps(attenuation_predictor_func)
    def wrapper(self: SupportsForecasting, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions):
        if self.is_a_fully_retracted_state(attenuator_motor_positions=attenuator_motor_positions):
            return EnergySpecificAttenuation.transparently_not_attenuating(energy_kev=energy_kev)
        elif self.is_an_energy_appropriate_state(energy_kev=energy_kev, attenuator_motor_positions=attenuator_motor_positions):
            return attenuation_predictor_func(energy_kev=energy_kev, attenuator_motor_positions=attenuator_motor_positions)
        else:
            raise IneligibleEnergyError(
                f"No valid forecast of attenuation at ineligible energy {energy_kev} keV given that at motor positions {attenuator_motor_positions}, there are unretracted absorbers."
            )
    return wrapper  # type: ignore[return-value]


class SupportsVariableAttenuation(Protocol):

    def can_accommodate(self, *, demand: EnergySpecificAttenuation) -> bool: ...

    def solve_for_swiftest_motor_shift(self, *, demand: EnergySpecificAttenuation, initial_motor_positions: AttenuatorMotorPositions) -> AttenuatorMotorPositions: ...


class BaseVariableAttenuation(SupportsVariableAttenuation, ABC):

    @abstractmethod
    def can_accommodate(self, *, demand: EnergySpecificAttenuation) -> bool: ...

    @abstractmethod
    def _find_swiftest_motor_changes_to_accommodate_demand(self, *, demand: EnergySpecificAttenuation, initial_motor_positions: AttenuatorMotorPositions) -> AttenuatorMotorPositions: ...

    @abstractmethod
    def _get_motor_positions_for_attenuator_retraction(self) -> AttenuatorMotorPositions: ...

    def solve_for_swiftest_motor_shift(self, *, demand: EnergySpecificAttenuation, initial_motor_positions: AttenuatorMotorPositions) -> AttenuatorMotorPositions:
        if self.can_accommodate(demand=demand):
            return self._find_swiftest_motor_changes_to_accommodate_demand(
                demand=demand, initial_motor_positions=initial_motor_positions
            )
        else:
            return self._get_motor_positions_for_attenuator_retraction()



class SystemWheel(SupportsForecasting):
    ...




class SystemWedge(SupportsForecasting, BaseVariableAttenuation):

    def __init__(self,
                 *,
                 absorber_calculator: VariableDepth,
                 motor_positioning_logic: WedgeMotorPositionalLogic,
                 ):
        self.absorber_logic = self._AuxiliaryCalculator(
            variable_absorber=absorber_calculator,
            motor_positioning_logic=motor_positioning_logic
        )
        self.positions_logic = motor_positioning_logic

    def accommodate(self, *, demand: EnergySpecificAttenuation) -> AttenuatorMotorPositions:
        fractional_motor_position = (
            self.absorber_logic.get_accommodating_lateral_position_mm(
                demand=demand
            )
        )
        if fractional_motor_position is None:
            return self._get_motor_positions_for_attenuator_retraction()

        return self._wrap_accommodating_wedge_position(
            fractional_motor_position=fractional_motor_position
        )

    def can_accommodate(self, *, demand: EnergySpecificAttenuation) -> bool:
        return self.absorber_logic.can_accommodate(demand=demand)

    def _find_swiftest_motor_changes_to_accommodate_demand(self, *, demand: EnergySpecificAttenuation, initial_motor_positions: AttenuatorMotorPositions) -> AttenuatorMotorPositions:
        return self.accommodate(demand=demand)

    def _get_motor_positions_for_attenuator_retraction(self) -> AttenuatorMotorPositions:
        return self.positions_logic.retracted_motor_positions()

    def _wrap_accommodating_wedge_position(self, *, fractional_motor_position: float) -> AttenuatorMotorPositions:
        best_match_wedge_motor_position_mm = (
            self.positions_logic.get_wedge_coordinates().parametric_lateral_position(
                parametric_fraction=fractional_motor_position
            )
        )
        return (
            self.positions_logic.wrap_raw_motor_position_mm(
                raw_position_mm=best_match_wedge_motor_position_mm
            )
        )

    class _AuxiliaryCalculator:

        def __init__(self,
                    *,
                    variable_absorber: VariableDepth,
                    motor_positioning_logic: WedgeMotorPositionalLogic):
            self.variable_depth_absorber = variable_absorber
            motor_coordinates = motor_positioning_logic.get_wedge_coordinates()
            self._threshold: Final[float] = (
                motor_coordinates.wedge_lateral_position_on_threshold()
            )
            self._max: Final[float] = (
                motor_coordinates.wedge_lateral_position_for_maximum_thickness()
            )

        def _calculate_required_fraction_of_absorption_capacity(
                self,
                *,
                threshold_bn: float,
                demand: EnergySpecificAttenuation
            ) -> float:
            max_bn = self.variable_depth_absorber.calculate_absorption_bn(
                xray_energy_kev=demand.energy_kev,
                motor_position_mm=self._max,
            )
            available_absorptions = ClosedInterval(
                lower = threshold_bn,
                upper=max_bn
            )
            p = parametric_fraction(
                interval = available_absorptions,
                value = demand.attenuation_bn
            )
            return min(p, 1.0,)  # coerce to the max absorption


        def _suitable_absorption_threshold_bn(
            self,
            *,
            demand: EnergySpecificAttenuation
        ) -> float|None:
            """Evaluates energy eligibility of the demand with respect to the material spectrum of the wedge.

            Returns:
                Threshold attenuation for the wedge, only if the demand can be accommodated.
            """
            if not self.variable_depth_absorber.is_eligible_for_energy(xray_energy_kev=demand.energy_kev):
                return None

            threshold_absorption = (
                self.variable_depth_absorber.calculate_absorption_bn(
                    xray_energy_kev=demand.energy_kev,
                    motor_position_mm=self._threshold,
                )
            )
            return (
                threshold_absorption
                if threshold_absorption > demand.attenuation_bn
                else None
            )

        def can_accommodate(self, *, demand: EnergySpecificAttenuation) -> bool:
            """That absorption is modelled at demand energy and threshold absorption is not larger than demand."""
            return self._suitable_absorption_threshold_bn(demand=demand) is not None


        def get_accommodating_lateral_position_mm(self, *, demand: EnergySpecificAttenuation) -> float|None:
            """Parameterise demand, normalised by dynamic range of linear wedge characteristics.

            Returns:
                A fraction of the wedge dynamic range, only if the demand can be accommodated.

            Note:
                This leans heavily on two linearities:
                1. That the absorption in logarithmic units is linear w.r.t. absorber thickness.
                2. That wedge taper maps differential absorber thickness change to lateral motor displacement.

                Thus changes in lateral motor position -> changes in thickness -> changes in absorption in Bn,
                are all linearly related, with a fraction of one range being the same fraction in the other two.
            """
            threshold_bn = (
                self._suitable_absorption_threshold_bn(demand=demand)
            )
            if threshold_bn is None:
                return None  # the wedge is too thick or not suited for the demand energy
            else:
                return (
                    self._calculate_required_fraction_of_absorption_capacity(
                        threshold_bn=threshold_bn,
                        demand=demand
                    )
                )


class WedgeOnlyAttenuatorTeam(SupportsForecasting, BaseVariableAttenuation):

    def __init__(self, system_wedge: SystemWedge):
        self.logical_wedge = system_wedge

    def _find_swiftest_motor_changes_to_accommodate_demand(self, *, demand: EnergySpecificAttenuation, initial_motor_positions: AttenuatorMotorPositions) -> AttenuatorMotorPositions:
        return self.logical_wedge.accommodate(demand=demand)

    def can_accommodate(self, *, demand: EnergySpecificAttenuation) -> bool:
        return self.logical_wedge.can_accommodate(demand=demand)

    def is_an_energy_appropriate_state(self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions) -> bool:
        return self.logical_wedge.is_an_energy_appropriate_state(
            energy_kev=energy_kev,
            attenuator_motor_positions=attenuator_motor_positions
        )

    def is_a_fully_retracted_state(self, *, attenuator_motor_positions: AttenuatorMotorPositions) -> bool:
        return self.logical_wedge.is_a_fully_retracted_state(attenuator_motor_positions=attenuator_motor_positions)

    # Intentionally not decorated with transparent_when_retracted
    # Any such decoration here would redundantly duplicate the decoration of the prediction method on the wedge
    def predict_attenuation_bn(self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions) -> EnergySpecificAttenuation:
        return self.logical_wedge.predict_attenuation_bn(
            energy_kev=energy_kev,
            attenuator_motor_positions=attenuator_motor_positions,
        )


class WedgeWheelAttenuatorTeam(SupportsForecasting):

    def __init__(self, *, system_wedge: SystemWedge, system_wheel: SystemWheel):
        self.logical_wedge = system_wedge
        self.logical_wheel = system_wheel

    @transparent_when_retracted
    def predict_attenuation_bn(self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions) -> EnergySpecificAttenuation:
        return self.logical_wedge.predict_attenuation_bn(
            energy_kev=energy_kev,
            attenuator_motor_positions=attenuator_motor_positions,
        )
