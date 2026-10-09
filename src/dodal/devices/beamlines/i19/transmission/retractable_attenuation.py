
from typing import Protocol, runtime_checkable

from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)

# Internal Protocols upon which the module level AP depends

class RetractableAttenuation(Protocol):
    """A wheel or wedge which has an attenuation calculator and a retracted OUT position."""

    async def is_retracted(self) -> bool: ...

    async def is_validly_positioned(self) -> bool: ...

    async def get_attenuation_bn(self, *, energy_kev: float) -> float: ...

    def is_retracted_at(
        self, *, hypothetical_motor_positions: AttenuatorMotorPositions
    ) -> bool: ...

    def predict_attenuation_at(
        self,
        *,
        energy_kev: float,
        hypothetical_motor_positions: AttenuatorMotorPositions,
    ) -> float: ...

    def would_be_eligible_at(
        self,
        *,
        energy_kev: float,
        hypothetical_motor_positions: AttenuatorMotorPositions,
    ) -> bool: ...


@runtime_checkable
class LogicalWedge(RetractableAttenuation, Protocol):
    """A retractable, variable attenuator mounted on a linear motor with continous positions."""

    async def current_motor_position(self) -> AttenuatorMotorPositions: ...

    def accommodate_demand(
        self,
        attenuation_demand_bn: float,
        *,
        energy_kev: float,
    ) -> AttenuatorMotorPositions:
        """If wedge can accommodate this demand, provide motor position solution.

        Args:
            attenuation_demand_bn:
                Target in logarithmic Barnett attenuation units.
            energy_kev:
                X-ray photon energy in kiloelectronvolts.

        Returns:
            Positional solution for the wedge to meet the demand.

        Raises:
            IneligibleMaterialError if the wedge material is ineligible at this energy.
        """
        ...


    def can_accommodate(
        self, attenuation_demand_bn: float, *, energy_kev: float
    ) -> bool: ...

    def retracted_position(self) -> AttenuatorMotorPositions: ...

    def merge_in_retraction_motor_position(self, *, other_motor_positions: AttenuatorMotorPositions | None) -> AttenuatorMotorPositions: ...


@runtime_checkable
class LogicalWheel(RetractableAttenuation, Protocol):
    """An indexed set of wheel mounted fixed attenuators with one index reserved for the non-absorbing retraction state."""

    async def current_index_position(self) -> AttenuatorMotorPositions: ...

    def retracted_index(self) -> int: ...

    def post_filter_attenuation_residuals_bn(
        self, attenuation_demand_bn: float, *, energy_kev: float
    ) -> list[float]: ...

    def merge_in_empty_slot_reserved_indexed_position(self, *, other_positions: AttenuatorMotorPositions) -> AttenuatorMotorPositions: ...




