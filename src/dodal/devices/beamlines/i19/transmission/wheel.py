from typing import Any

from ophyd_async.core import StrictEnum, SubsetEnum
from pydantic import PositiveInt, StrictFloat, StrictInt

from dodal.devices.attenuator.filter import FilterWheel
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
    PermittedKeyStr,
)
from dodal.devices.beamlines.i19.transmission.filter_wheel_slot_occupancy import (
    FilterWheelSlotOccupancy,
)
from dodal.devices.beamlines.i19.transmission.retractable_attenuation import (
    LogicalWheel,
)
from dodal.devices.beamlines.i19.transmission.transmission_api import IndexedReadable


class _BaseLogicalWheel(LogicalWheel):
    def __init__(
        self, *, wheel_identifier: PermittedKeyStr, occupancy: FilterWheelSlotOccupancy
    ):
        self._identifier = wheel_identifier
        self._occupancy = occupancy

    # Unimplemented abstract methods - to be covered in child classes

    async def _read_current_index(self) -> int: ...

    def _predict_attenuation_using_slot_at(
        self, *, energy_kev: float, index: int, strict: bool
    ) -> float: ...

    # Implemented async API methods ( defined in Protocol LogicalWheel )

    async def current_index_position(self) -> AttenuatorMotorPositions:
        latest_valid_index = await self._read_and_verify_current_index()
        return self._wrap_index_as_motor_position_for_this_wheel(
            a_given_index=latest_valid_index
        )

    async def get_attenuation_bn(self, *, energy_kev: float) -> float:
        latest_index = await self._read_current_index()
        self._raise_exception_if_wheel_in_forbidden_state(latest_index=latest_index)
        return self._predict_attenuation_using_slot_at(
            energy_kev=energy_kev, index=latest_index, strict=True
        )

    async def is_retracted(self) -> bool:
        current_wheel_index = await self._read_current_index()
        return self._occupancy.is_retracted_at(index=current_wheel_index)

    async def is_validly_positioned(self, *, strict: bool = True) -> bool:
        current_wheel_index = await self._read_current_index()
        return self._occupancy.is_index_in_use(index=current_wheel_index, strict=strict)

    def merge_in_empty_slot_reserved_indexed_position(
        self, *, other_positions: AttenuatorMotorPositions | None
    ) -> AttenuatorMotorPositions:
        return (
            self._wrap_index_as_motor_position_for_this_wheel(
                a_given_index=self._occupancy.reserved_slot
            )
            | other_positions
        )

    def predict_attenuation_at(
        self,
        *,
        energy_kev: float,
        hypothetical_motor_positions: AttenuatorMotorPositions,
    ) -> float:
        index_arg = self._extract_wheel_specific_index_from_motor_positions(
            motor_positions=hypothetical_motor_positions,
        )
        return self._predict_attenuation_using_slot_at(
            energy_kev=energy_kev,
            index=index_arg,
            strict=True,
        )

    def retracted_index(self) -> int:
        return self._occupancy.reserved_slot

    def _extract_wheel_specific_index_from_motor_positions(
        self, *, motor_positions: AttenuatorMotorPositions
    ) -> PositiveInt:
        index: StrictInt | StrictFloat = motor_positions.validated_and_complete[
            self._identifier
        ]
        if not isinstance(index, int) or index < 1:
            raise ValueError(
                f"Motor positions contains invalid wheel index {index} which is not a positive (non-zero) integer."
            )
        return int(index)

    def post_filter_attenuation_residuals_bn(
        self, attenuation_demand_bn: float, *, energy_kev: float
    ) -> dict[PositiveInt, float]:
        # N.B. the empty slot has its own calculator - eligible at all energies
        # Here the empty slot is made an honorary foil - for naming brevity's sake
        foil_calculators = self._occupancy.active_slots_attenuation_calculators(
            strict=True
        )
        # Only calculate residuals for energy eligible foils
        reductions_bn = {
            index: calc.calculate_absorption_bn(xray_energy_kev=energy_kev)
            for index, calc in foil_calculators.items()
            if calc.is_eligible_for_energy(xray_energy_kev=energy_kev)
        }
        # Exclude foils which attenuate more than demanded
        return {
            index: (attenuation_demand_bn - reduction_bn)
            for index, reduction_bn in reductions_bn.items()
            if not attenuation_demand_bn < reduction_bn
        }

    def wrap_wheel_index(
        self, *, wheel_index: PositiveInt | None
    ) -> AttenuatorMotorPositions:
        if wheel_index is None:
            wheel_index = self._occupancy.reserved_slot
        return self._wrap_index_as_motor_position_for_this_wheel(
            a_given_index=wheel_index
        )

    def _raise_exception_if_wheel_in_forbidden_state(
        self, *, latest_index: int, strict: bool = True
    ) -> None:
        if not self._occupancy.is_index_in_use(index=latest_index, strict=strict):
            _msg: str = f"Present index {latest_index} of wheel {self._identifier} is forbidden."
            raise RuntimeError(_msg)

    async def _read_and_verify_current_index(self, *, strict: bool = True) -> int:
        latest_index = await self._read_current_index()
        self._raise_exception_if_wheel_in_forbidden_state(
            latest_index=latest_index, strict=strict
        )
        return latest_index

    def _wrap_index_as_motor_position_for_this_wheel(
        self, *, a_given_index: PositiveInt
    ) -> AttenuatorMotorPositions:
        return AttenuatorMotorPositions(
            discrete_indices={self._identifier: a_given_index},
        )


class IndexedWheelPositionReadable(IndexedReadable):
    """Wraps FilterWheel converting reads from raw readout to motor index."""

    def __init__(self, *, readable_filter_wheel: FilterWheel):
        self.readable = readable_filter_wheel
        self.wheel_position_mapping: dict[StrictEnum | SubsetEnum, int] = {
            enum_member: index
            for index, enum_member in enumerate(
                readable_filter_wheel.filter_selections, start=1
            )
        }

    @staticmethod
    def _extract_wheel_index(raw_readout: dict[str, Any]) -> StrictEnum | SubsetEnum:
        signal_data = next(iter(raw_readout.values()))
        return signal_data["value"]

    async def read_indexed_position(self) -> int:
        raw_readout: dict[str, Any] = await self.readable.read()
        extracted_position = self._extract_wheel_index(raw_readout)
        return self.wheel_position_mapping[extracted_position]


class LogicalAttenuatingFilterWheel(_BaseLogicalWheel):
    def __init__(
        self,
        *,
        wheel_identifier: PermittedKeyStr,
        occupancy: FilterWheelSlotOccupancy,
        index_readable: IndexedReadable,
    ):
        self._readable = index_readable
        super().__init__(occupancy=occupancy, wheel_identifier=wheel_identifier)

    async def _read_current_index(self) -> int:
        return await self._readable.read_indexed_position()

    def _predict_attenuation_using_slot_at(
        self, *, energy_kev: float, index: int, strict: bool
    ) -> float:
        calc = self._occupancy.absorption_calculator_of(index=index, strict=strict)
        return calc.calculate_absorption_bn(xray_energy_kev=energy_kev)
