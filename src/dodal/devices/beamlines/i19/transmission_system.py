
from typing import Annotated, Protocol

from pydantic import Field, StrictFloat, StrictInt, TypeAdapter, validate_call
from pydantic.dataclasses import dataclass

from dodal.common.general_maths.absorbers import FixedDepth, XrayEnergy
from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
    Attenuation_Bn,
)

from .access_controlled.attenuator_motor_squad import (
    AttenuatorMotorPositions,
    PermittedKeyStr,
)

Wheel_Index = Annotated[StrictInt, Field(gt=0, lt=21)]

wheel_index_adapter: TypeAdapter[Wheel_Index] = TypeAdapter(Wheel_Index)

class EmptyFilterSlot(FixedDepth):

    @validate_call
    def calculate_absorption_bn(self, *, xray_energy_kev: XrayEnergy) -> Attenuation_Bn:
        return CANONICAL_NON_ABSORPTION


class IndexReader(Protocol):

    def read_wheel_index(self):
        ...


class IndexedFilterSet(Protocol):

    def are_absorbers_out_of_beam_at_index(self, index: Wheel_Index) -> bool:
        ...

    @validate_call
    def filter_at(self, index: Wheel_Index) -> FixedDepth:
        ...


class WheelOneFilterSet(IndexedFilterSet):

    def __init__(self)
        self._empty_slot_equivalent_absorber: FixedDepth = EmptyFilterSlot()
        self._canonical_empty_slot: Wheel_Index = 1 # AIR1

    def _canonical_wheel_name(self) -> str:
        return "Filter Wheel One"


    def _get_populated_slot_indices(self) -> set[Wheel_Index]:
        return set()  # TODO populate these by reverse engineering content of filter_selections - when wheel works


    def canonical_index_for_absorbers_out_of_beam(self) -> Wheel_Index:
        return self._canonical_empty_slot


    @validate_call
    def are_absorbers_out_of_beam_at_index(self, index: Wheel_Index) -> bool:
        return self.canonical_index_for_absorbers_out_of_beam == index


    @validate_call
    def filter_at(self, index: Wheel_Index) -> FixedDepth:
        match index:
            case self._canonical_empty_slot:
                return self._empty_slot_equivalent_absorber
            case _ if index in self._get_populated_slot_indices():
                _not_implemented_msg = "Populated slots are presently unsupported in {self._get_wheel_name()}"
                raise NotImplementedError(_not_implemented_msg)
            case _:
                _unused_msg = f"{self._canonical_wheel_name()}, does not use slot {index}."
                raise ValueError(_unused_msg)


@dataclass(kw_only=True, frozen=True)
class AttenuationRequest:
    """Pairing off, of an x-ray energy and requested attenuation.

    Features system friendly capacity to calculate remainder requests, based on reductions from allocated absorption.

    Args:
        energy_kev: The x-ray energy relevant for the requested attenuation.
        target_bn: The remaining attenuation from the system budget that we want to burn.
    """

    xray_energy_kev: XrayEnergy
    target_bn: Attenuation_Bn

    @validate_call
    def _calculate_residual_bn(
        self,
        satisfied_attenuation_bn: Annotated[StrictFloat, Field(ge=0.0)],
    ) -> Attenuation_Bn:
        """Internal method to calculate burn down of attenuation budget in request.

        Args:
            satisfied_attenuation_bn:  The latest reduction in the unsatisfied request which is about to be met.

        Returns:
            the reduced attenuation demand, reduced by the satisfied portion.
        """
        return self.target_bn - satisfied_attenuation_bn

    @validate_call
    def calculate_remaining_request(
        self,
        satisfied_attenuation_bn: Attenuation_Bn
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
        return AttenuationRequest(xray_energy_kev=self.xray_energy_kev, target_bn=_residual_bn)


@dataclass(kw_only=True, frozen=True)
class AttenuationMatch:
    request: AttenuationRequest
    closest_attenuation_bn: Attenuation_Bn
    implementation: AttenuatorMotorPositions


class Attenuator(Protocol):

    @validate_call
    def calculate_attenuation_bn(
        self,
        xray_energy_kev: XrayEnergy,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> Attenuation_Bn:
        """API: Calculate attenuation contribution at x-ray energy & motor positions.

        This hypothetical estimator will decide which motors are relevant,
        and compound Attenuators are going to sum over the results from each element.

        Args:
            xray_energy_kev: Hypothetical x-ray energy in kiloelectronvolts.
            attenuator_positions: Hypothetical motor positions.

        Returns:
            0.0 Bn if relevant motor position is (positions are) OUT, (or absent),
                otherwise a calculated absorption for the hypothetical situation.
        """
        ...

    @validate_call
    def is_in_the_out_position(self) -> bool:
        """API: Reports if an attenuating contribution is excluded by the absorber being stowed in the OUT position.

        Canonically defined OUT positions are provided for all absorbers and compound sub-systems of absorbers.
        """
        ...

class AttenuatorSubsystem(Attenuator):

    @validate_call
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
        ...


class FilterWheel(Attenuator):

    @validate_call
    def __init__(self,
                 recognised_filters: IndexedFilterSet,
                 motor_key: PermittedKeyStr,
                 index_reader: IndexReader):
        self.name_of_motor: PermittedKeyStr = motor_key
        self.absorbing_filters: IndexedFilterSet = recognised_filters
        self.wheel_reader: IndexReader = index_reader

    def _filter_at(self, wheel_index: Wheel_Index) -> FixedDepth:
        return self.absorbing_filters.filter_at(wheel_index)


    def calculate_attenuation_bn(
        self,
        xray_energy_kev: XrayEnergy,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> Attenuation_Bn:
        """Estimates foil attenuation at x-ray energy assuming input wheel position.

        N.B. If the wheel motor position is absent from the attenuator motor positions,
        this will return the OUT position value.

        Args:
            xray_energy_kev: The x-ray energy in kiloelectronvolts.
            attenuator_positions: Motor positions for the calculation.

        Returns:
            0.0 Bn if position is absent or OUT, otherwise a calculated foil absorption.
        """
        _motor_positions = attenuator_positions.validated_complete_demand()
        _raw_wheel_index = _motor_positions[self.name_of_motor]
        _wheel_index: Wheel_Index = wheel_index_adapter.validate_python(_raw_wheel_index)

        if self.is_in_the_out_position():
            return CANONICAL_NON_ABSORPTION

        _selected_filter: FixedDepth = self._filter_at(_wheel_index)
        return _selected_filter.calculate_absorption_bn(xray_energy_kev=xray_energy_kev)


    def is_in_the_out_position(self, wheel_index:Wheel_Index) -> bool:
        return self.absorbing_filters.are_absorbers_out_of_beam_at_index(wheel_index)


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
