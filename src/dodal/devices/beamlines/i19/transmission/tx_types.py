
from typing import Annotated, Protocol, runtime_checkable

from pydantic import Field, StrictFloat, StrictInt, TypeAdapter, validate_call
from pydantic.dataclasses import dataclass

from dodal.common.general_maths.absorbers import FixedDepth, VariableDepth, WedgeMotorScaleSpec, XrayEnergy
from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
    Attenuation_Bn,
)
from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorPositions,
    PermittedKeyStr,
)

# General types
# Hardware specifics for I19 in system_specifics.py

LARGEST_WHEEL_SIZE=12

Wheel_Index = Annotated[StrictInt, Field(gt=0, le=LARGEST_WHEEL_SIZE)]

wheel_index_adapter: TypeAdapter[Wheel_Index] = TypeAdapter(Wheel_Index)

class EmptyFilterSlot(FixedDepth):

    @validate_call
    def calculate_absorption_bn(self, *, xray_energy_kev: XrayEnergy) -> Attenuation_Bn:
        return CANONICAL_NON_ABSORPTION


class IndexReader(Protocol):

    def read_motor_index(self) -> Wheel_Index:
        ...


class IndexedFilterSet(Protocol):

    def are_absorbers_out_of_beam_at_index(self, index: Wheel_Index) -> bool:
        ...

    @validate_call
    def filter_at(self, index: Wheel_Index) -> FixedDepth:
        ...


class PositionReader(Protocol):

    def read_motor_position_mm(self) -> float:
        ...


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
    def _calculate_absorption(
        self,
        *,
        xray_energy_kev: XrayEnergy,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> Attenuation_Bn:
        """API: Calculate attenuation contribution at x-ray energy & (not OUT) motor positions.

        This hypothetical estimator will decide which motors are relevant,
        and compound Attenuators are going to sum over the results from each element.

        Args:
            xray_energy_kev: Hypothetical x-ray energy in kiloelectronvolts.
            attenuator_positions: Hypothetical motor positions.

        Returns:
            calculated absorption for the hypothetical situation,
            should only be called if the motor positions are not OUT.
        """
        ...

    @validate_call
    def are_consistent_with_absorber_removed(self,
                                              *,
                                              attenuator_positions:AttenuatorMotorPositions) -> bool:
        ...

    @validate_call
    def calculate_attenuation_bn(
        self,
        *,
        xray_energy_kev: XrayEnergy,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> Attenuation_Bn:
        if self.are_consistent_with_absorber_removed(attenuator_positions=attenuator_positions):
            return CANONICAL_NON_ABSORPTION
        else:
            return self._calculate_absorption(xray_energy_kev=xray_energy_kev,
                                              attenuator_positions=attenuator_positions,)


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


class Wedge(Attenuator):

    @validate_call
    def __init__(self,
                 *,
                 motor_scale: WedgeMotorScaleSpec,
                 motor_key: PermittedKeyStr,
                 position_reader: PositionReader,
                 absorber: VariableDepth):
        self.name_of_motor: PermittedKeyStr = motor_key
        self.scale: WedgeMotorScaleSpec = motor_scale
        self.absorber: VariableDepth = absorber
        self.motor_position_reader = position_reader

    def _consistent_with_absorber_removed(self, *, motor_position_mm:StrictFloat) -> bool:
        return self.scale.is_position_consistent_with_absorber_removed(motor_position_mm=motor_position_mm):

    def _calculate_absorption(
        self,
        *,
        xray_energy_kev: XrayEnergy,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> Attenuation_Bn:
        _motor_positions = attenuator_positions.validated_complete_demand()
        _raw_position_mm: StrictFloat = _motor_positions[self.name_of_motor]
        return self.absorber.calculate_absorption_bn(xray_energy_kev=xray_energy_kev,
                                                     motor_position_mm=_raw_position_mm)

    @validate_call
    def are_consistent_with_absorber_removed(self,
                                             *,
                                             attenuator_positions:AttenuatorMotorPositions) -> bool:
        _motor_positions = attenuator_positions.validated_complete_demand()
        _raw_position_mm: StrictFloat = _motor_positions[self.name_of_motor]
        return self._consistent_with_absorber_removed(motor_position_mm=_raw_position_mm)


    def is_in_the_out_position(self) -> bool:
        _latest_position = self.motor_position_reader.read_motor_position_mm()
        return self._consistent_with_absorber_removed(motor_position_mm=_latest_position)


class Wheel(Attenuator):

    @validate_call
    def __init__(self,
                 *,
                 recognised_filters: IndexedFilterSet,
                 motor_key: PermittedKeyStr,
                 index_reader: IndexReader):
        self.name_of_motor: PermittedKeyStr = motor_key
        self.absorbing_filters: IndexedFilterSet = recognised_filters
        self.wheel_reader: IndexReader = index_reader

    def _filter_at(self, wheel_index: Wheel_Index) -> FixedDepth:
        return self.absorbing_filters.filter_at(wheel_index)

    def _consistent_with_absorber_removed(self, *, wheel_index:Wheel_Index) -> bool:
        return self.absorbing_filters.are_absorbers_out_of_beam_at_index(wheel_index)

    def _calculate_absorption(
        self,
        *,
        xray_energy_kev: XrayEnergy,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> Attenuation_Bn:
        """Estimates foil attenuation at x-ray energy assuming input wheel position is not OUT.

        Args:
            xray_energy_kev: The x-ray energy in kiloelectronvolts.
            attenuator_positions: Motor positions for the calculation.

        Returns:
            a calculated foil absorption.
        """
        _motor_positions = attenuator_positions.validated_complete_demand()
        _raw_wheel_index = _motor_positions[self.name_of_motor]
        _wheel_index: Wheel_Index = wheel_index_adapter.validate_python(_raw_wheel_index)

        _selected_filter: FixedDepth = self._filter_at(_wheel_index)
        return _selected_filter.calculate_absorption_bn(xray_energy_kev=xray_energy_kev)

    @validate_call
    def are_consistent_with_absorber_removed(self,
                                             *,
                                             attenuator_positions:AttenuatorMotorPositions) -> bool:
        _motor_positions = attenuator_positions.validated_complete_demand()
        _raw_wheel_index = _motor_positions[self.name_of_motor]
        _wheel_index: Wheel_Index = wheel_index_adapter.validate_python(_raw_wheel_index)
        return self._consistent_with_absorber_removed(wheel_index=_wheel_index)


    def is_in_the_out_position(self) -> bool:
        """API of any Attenuator - asks if it has been removed from the x-ray beam.

        When this reports True, there is no need for any energy specific absorption calculations.
        """
        _motor_index = self.wheel_reader.read_motor_index()
        return self._consistent_with_absorber_removed(wheel_index=_motor_index)


