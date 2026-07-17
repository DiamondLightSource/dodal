from abc import ABC, abstractmethod
from typing import Annotated, Protocol

from pydantic import Field, StrictFloat, StrictInt
from pydantic.dataclasses import dataclass

from dodal.common.general_maths.absorbers import (
    ThicknessProvider,
)

from .access_controlled.attenuator_motor_squad import AttenuatorMotorPositions


@dataclass(kw_only=True, frozen=True)
class AttenuationRequest:
    """Pairing off, of an x-ray energy and requested attenuation.

    Features system friendly capacity to calculate remainder requests, based on reductions from allocated absorption.

    Args:
        energy_kev: The x-ray energy relevant for the requested attenuation.
        target_bn: The remaining attenuation from the system budget that we want to burn.
    """

    energy_kev: StrictFloat | StrictInt
    target_bn: Annotated[StrictFloat | StrictInt, Field(ge=0.0)]

    def _calculate_residual_bn(
        self,
        satisfied_attenuation_bn: Annotated[StrictFloat | StrictInt, Field(ge=0.0)],
    ) -> float:
        """Internal method to calculate burn down of attenuation budget in request.

        Args:
            satisfied_attenuation_bn:  The latest reduction in the unsatisfied request which is about to be met.

        Returns:
            the reduced attenuation demand, reduced by the satisfied portion.
        """
        return self.target_bn - satisfied_attenuation_bn

    def calculate_remaining_request(
        self,
        satisfied_attenuation_bn: Annotated[StrictFloat | StrictInt, Field(ge=0.0)],
    ) -> "AttenuationRequest":
        """Generates new request with the remaining (unmet) attenuation demand, given a certain amount has already been satisfied.

        Args:
            satisfied_attenuation_bn: The amount of attenuation (Barnett units) already covered by absorbers considered.

        Return:
            Amortized version of the original request, with only the unmet portion of the original absorption budget.

        Raises:
            Will raise Validation error if the satisfied attenuation exceeds the original budget.
        """
        _residual_bn = self._calculate_residual_bn(satisfied_attenuation_bn)
        return AttenuationRequest(energy_kev=self.energy_kev, target_bn=_residual_bn)


@dataclass(kw_only=True, frozen=True)
class AttenuationMatch:
    request: AttenuationRequest
    closest_attenuation_bn: float
    implementation: AttenuatorMotorPositions


class Attenuator(ABC):
    @abstractmethod
    def calculate_attenuation_bn(
        self,
        energy_kev: StrictFloat | StrictInt,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> float:
        """API: Calculate attenuation contribution at x-ray energy & motor positions.

        This hypothetical estimator will decide which motors are relevant,
        and compound Attenuators are going to sum over the results from each element.

        Args:
            energy_kev: Hypothetical x-ray energy in kiloelectronvolts.
            attenuator_positions: Hypothetical motor positions.

        Returns:
            0.0 Bn if relevant motor position is (positions are) OUT, (or absent),
                otherwise a calculated absorption for the hypothetical situation.
        """


class AttenuatorSubsystem(Attenuator):
    @abstractmethod
    def predict_efficient_match(self, request: AttenuationRequest) -> AttenuationMatch:
        """Reports nearest reachable attenuation of the subsystem (in Barnett Units), at input energy.

        The calculation is based on restrictions imposed on,
        permitted motor positions,
        and suitability of absorbers for particular energy ranges.

        Args:
            request: The requested attenuation and energy

        Returns:
            Summary of the nearest achievable solution.
        """


@dataclass(kw_only=True, frozen=True)
class FoilFilter:
    def __init__(self, geometry: ThicknessProvider):
        pass


class IndexedFilterSet(Protocol):
    def filter_at(self, index: Annotated[StrictInt, Field(gt=0)]) -> FoilFilter: ...


class WheelOneFilterSet:
    def filter_at(self, index: Annotated[StrictInt, Field(gt=0)]):
        return None


class FilterWheel(Attenuator):
    def __init__(self, filter_indexing: IndexedFilterSet, motor_key: str = "w"):
        self.name_of_motor: str = motor_key
        self.filter_indexing = filter_indexing

    def _filter_at(self, wheel_index: StrictInt) -> FoilFilter:
        return self.filter_indexing.filter_at(wheel_index)

    def calculate_attenuation_bn(
        self,
        energy_kev: StrictFloat | StrictInt,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> float:
        """Estimates foil attenuation at x-ray energy assuming input wheel position.

        N.B. If the wheel motor position is absent from the attenuator motor positions,
        this will return the OUT position value.

        Args:
            energy_kev: The x-ray energy in kiloelectronvolts.
            attenuator_positions: Motor positions for the calculation.

        Returns:
            0.0 Bn if position is absent or OUT, otherwise a calculated foil absorption.
        """
        _motor_positions = attenuator_positions.validated_complete_demand()
        try:
            _wheel_index = _motor_positions[self.name_of_motor]
            return self.filter_at(_wheel_index).get_attenuation(energy_kev)
        except KeyError as _relevant_motor_not_found:
            return 0.0


class PrimaryAttenuators(AttenuatorSubsystem):
    def __init__(
        self,
    ):
        pass

    def calculate_attenuation_bn(
        self,
        energy_kev: StrictFloat | StrictInt,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> float:
        return 0.0  # TODO - write this
