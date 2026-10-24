
from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from typing import Final, Protocol, TypeVar

from dodal.common.general_maths.absorbers import VariableDepth
from dodal.common.general_maths.material_absorption_maths import IneligibleEnergyError
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.attenuation_forecasting import (
    BaseForecasting,
    SupportsForecasting,
)
from dodal.devices.beamlines.i19.transmission.energy_specific_attenuation import (
    EnergySpecificAttenuation,
)
from dodal.devices.beamlines.i19.transmission.wedge_motor_positional_logic import (
    WedgeMotorPositionalLogic,
)

P = TypeVar("P", bound=Callable[..., EnergySpecificAttenuation])

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

    def accommodate(self, *, demand: EnergySpecificAttenuation) -> AttenuatorMotorPositions: ...

    def can_accommodate(self, *, demand: EnergySpecificAttenuation) -> bool: ...

    def solve_for_swiftest_motor_shift(self, *, demand: EnergySpecificAttenuation, initial_motor_positions: AttenuatorMotorPositions) -> AttenuatorMotorPositions: ...


class BaseVariableAttenuation(ABC, SupportsVariableAttenuation):

    @abstractmethod
    def accommodate(self, *, demand: EnergySpecificAttenuation) -> AttenuatorMotorPositions: ...

    @abstractmethod
    def can_accommodate(self, *, demand: EnergySpecificAttenuation) -> bool: ...

    @abstractmethod
    def _find_swiftest_motor_changes_to_accommodate_demand(self, *, demand: EnergySpecificAttenuation, initial_motor_positions: AttenuatorMotorPositions) -> AttenuatorMotorPositions: ...

    @abstractmethod
    def _get_retracted_motor_positions(self) -> AttenuatorMotorPositions: ...

    def solve_for_swiftest_motor_shift(self, *, demand: EnergySpecificAttenuation, initial_motor_positions: AttenuatorMotorPositions) -> AttenuatorMotorPositions:
        if self.can_accommodate(demand=demand):
            return self._find_swiftest_motor_changes_to_accommodate_demand(
                demand=demand, initial_motor_positions=initial_motor_positions
            )
        else:
            return self._get_retracted_motor_positions()



class SystemWheel(SupportsForecasting):
    ...

class SystemWedge(SupportsForecasting, BaseVariableAttenuation):

    def __init__(self,
                 *,
                 absorber_calculator: VariableDepth,
                 motor_positioning_logic: WedgeMotorPositionalLogic,
                 ):
        self.motor_logic: Final[WedgeMotorPositionalLogic] = motor_positioning_logic
        self.absorption_calc: Final[VariableDepth] = absorber_calculator

    def accommodate(self, *, demand: EnergySpecificAttenuation) -> AttenuatorMotorPositions:
        self.absorption_calc.

    def can_accommodate(self, *, demand: EnergySpecificAttenuation) -> bool:
        return self.absorption_calc.

    def _find_swiftest_motor_changes_to_accommodate_demand(self, *, demand: EnergySpecificAttenuation, initial_motor_positions: AttenuatorMotorPositions) -> AttenuatorMotorPositions:
        return self.accommodate(demand=demand)

    def _get_retracted_motor_positions(self) -> AttenuatorMotorPositions:
        return self.motor_logic.retracted_motor_positions()


class WedgeOnlyAttenuatorTeam(BaseForecasting, BaseVariableAttenuation):

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

    # not decorated as that would be redundant, given delegation to the decorated wedge method
    def predict_attenuation_bn(self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions) -> EnergySpecificAttenuation:
        return self.logical_wedge.predict_attenuation_bn(
            energy_kev=energy_kev,
            attenuator_motor_positions=attenuator_motor_positions,
        )


class WedgeWheelAttenuatorTeam(BaseForecasting):

    def __init__(self, *, system_wedge: SystemWedge, system_wheel: SystemWheel):
        self.logical_wedge = system_wedge
        self.logical_wheel = system_wheel

    @transparent_when_retracted
    def predict_attenuation_bn(self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions) -> EnergySpecificAttenuation:
        return self.logical_wedge.predict_attenuation_bn(
            energy_kev=energy_kev,
            attenuator_motor_positions=attenuator_motor_positions,
        )
