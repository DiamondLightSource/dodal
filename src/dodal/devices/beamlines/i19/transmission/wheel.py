
from pydantic import StrictFloat, StrictInt

from dodal.devices.beamlines.i19.transmission.filter_wheel_slot_occupancy import FilterWheelSlotOccupancy

from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
    PermittedKeyStr,
)
from dodal.devices.beamlines.i19.transmission.retractable_attenuation import (
    LogicalWheel,
)

from dodal.common.general_maths.absorbers import FixedDepth

class _BaseIndexingWheel(LogicalWheel):

    def __init__(self, *, wheel_identifier: PermittedKeyStr, occupancy: FilterWheelSlotOccupancy):
        self._identifier = wheel_identifier
        self._occupancy = occupancy

    # Unimplemented abstract methods - to be covered in child classes

    async def _read_current_index(self) -> int: ...

    def _predict_attenuation_using_slot_at(self, *, energy_kev:float, index: int, strict: bool) -> float: ...

    # Implemented async API methods ( defined in Protocol LogicalWheel )

    async def current_index_position(self) -> AttenuatorMotorPositions:
        latest_valid_index = await self._read_and_verify_current_index()
        return (
            self._wrap_index_as_motor_position_for_this_wheel(
                a_given_index=latest_valid_index
            )
        )


    async def get_attenuation_bn(self, *, energy_kev: float) -> float:
        latest_index = await self._read_current_index()
        self._raise_exception_if_wheel_in_forbidden_state(latest_index=latest_index)
        return (
            self._predict_attenuation_using_slot_at(
                energy_kev=energy_kev,
                index=latest_index,
                strict=True
            )
        )


    async def is_retracted(self) -> bool:
        current_wheel_index = await self._read_current_index()
        return self._occupancy.is_retracted_at(index=current_wheel_index)


    async def is_validly_positioned(self, *, strict:bool=True) -> bool:
        current_wheel_index = await self._read_current_index()
        return self._occupancy.is_index_in_use(index=current_wheel_index, strict=strict)


    def _list_demand_residuals(self, attenuation_demand_bn: float, *, energy_kev: float
        ) -> dict[int, float]:
        _calculators = self._occupancy.active_slots_attenuation_calculators(strict=True)
        _reductions_bn = {
            index: calc.calculate_absorption_bn(xray_energy_kev=energy_kev)
            for index, calc in _calculators.items()
        }
        return {
            index: attenuation_demand_bn - reduction_bn
            for index, reduction_bn in _reductions_bn.items()
            if not attenuation_demand_bn < reduction_bn
        }

    def merge_in_empty_slot_reserved_indexed_position(
        self, *, other_positions: AttenuatorMotorPositions | None
    ) -> AttenuatorMotorPositions:
        return self._wrap_index_as_motor_position_for_this_wheel(
            a_given_index=self._occupancy.reserved_slot
        ) | other_positions


    def predict_attenuation_at(
        self,
        *,
        energy_kev: float,
        hypothetical_motor_positions: AttenuatorMotorPositions,
    ) -> float:
        index_arg = (
            self._extract_wheel_specific_index_from_motor_positions(
                motor_positions=hypothetical_motor_positions,
            )
        )
        return (
            self._predict_attenuation_using_slot_at(
                energy_kev=energy_kev,
                index=index_arg,
                strict=True,
            )
        )

    def retracted_index(self) -> int:
        return self._occupancy.reserved_slot


    def _extract_wheel_specific_index_from_motor_positions(self, *, motor_positions: AttenuatorMotorPositions) -> int:
         index: StrictInt | StrictFloat = motor_positions.validated_and_complete[self._identifier]
         if not isinstance(index, int):
             raise ValueError(f"Motor positions contains wheel index {index} which is not an integer.")
         return int(index)


    def _raise_exception_if_wheel_in_forbidden_state(self, *, latest_index: int, strict:bool=True) -> None:
        if not self._occupancy.is_index_in_use(index=latest_index, strict=strict):
            _msg: str = f"Present index {latest_index} of wheel {self._identifier} is forbidden."
            raise RuntimeError(_msg)


    async def _read_and_verify_current_index(self, *, strict:bool=True) -> int:
        latest_index = await self._read_current_index()
        self._raise_exception_if_wheel_in_forbidden_state(latest_index=latest_index, strict=strict)
        return latest_index


    def _wrap_index_as_motor_position_for_this_wheel(self, *, a_given_index: int) -> AttenuatorMotorPositions:
        return AttenuatorMotorPositions(
            discrete_indices={self._identifier: a_given_index},
        )


class AttenuatingFilterWheel(_BaseIndexingWheel):

    def __init__(self,
                 *,
                 wheel_identifier: PermittedKeyStr,
                 
