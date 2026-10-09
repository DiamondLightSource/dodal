from abc import ABC, abstractmethod
from typing import Final, final

from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.retractable_attenuation import (
    LogicalWedge,
    LogicalWheel,
    RetractableAttenuation,
)


class _BaseAttenuatorTeam(ABC):
    """Base of all implementations of the ( Transmission API ) AttenuatorTeam protocol.

    Note: Some methods, those with (near universal) internal self-dependencies,
    have their common implementations provided by this base class.
    """

    # Unimplemented async methods

    @abstractmethod
    async def current_motor_positions(self) -> AttenuatorMotorPositions:
        """Motor index or position read back of the motorised elements within the team."""
        ...

    @abstractmethod
    async def is_validly_positioned(self) -> bool:
        """Reports false if any of the motors are outside permitted indices or positions."""
        ...

    # Unimplemented sync methods

    @abstractmethod
    def would_be_fully_retracted_at(
        self, *, hypothetical_motor_positions: AttenuatorMotorPositions
    ) -> bool:
        """Checks given indices and positions for relevant motors of this team.

        Returns:
            True only if all motor positions and indices would be validly retracted.
        """
        ...


    @abstractmethod
    def can_accommodate(
        self, attenuation_demand_bn: float, *, energy_kev: float
    ) -> bool:
        """Used for fulcrum decisions, whether to meet a demand or retract this team.

        Returns:
            True if the team is eligible to meet the demanded attenuation at the given energy.
        """
        ...


    @abstractmethod
    def merge_in_retraction_motor_positions(
        self, *, other_motor_positions: AttenuatorMotorPositions | None = None
    ) -> AttenuatorMotorPositions:
        """Asks this team to merge its retraction positions into system-wide motor positions.

        Args:
            other_motor_positions:
                Any other teams' solutions (already calculated and merged) - Optional.

        Returns:
            Accumulation working towards a full-system motor solution,
            which may consist of other teams' solutions (already calculated and merged)
            merged in with this team's retraction positions.

        Note:
            This method is only called for teams that will be retracted.
        """
        ...


    @abstractmethod
    def predict_attenuation_at(
        self,
        *,
        energy_kev: float,
        hypothetical_motor_positions: AttenuatorMotorPositions,
    ) -> float:
        """Transparent when retracted or attenuation of active elements eligible at the energy range.

        Note:
            Any elements in a hypothetically active position, but ineligible at the x-ray energy,
            will lead to raised exceptions.
        """
        ...


    @abstractmethod
    def solve_swiftest_motor_shift(
        self,
        attenuation_demand_bn: float,
        *,
        energy_kev: float,
        starting_positions: AttenuatorMotorPositions,
    ) -> AttenuatorMotorPositions:
        """Either the fully retracted state for this team, or the active position most rapidly reached to best meet the demand."""
        ...

    # Methods that the base can implement by default

    async def get_attenuation_bn(self, *, energy_kev: float) -> float:
        """Uses the attenuation prediction calculator with the live motor position readback."""
        latest_motor_positions = await self.current_motor_positions()
        return self.predict_attenuation_at(
            energy_kev=energy_kev, hypothetical_motor_positions=latest_motor_positions
        )

    async def is_retracted(self) -> bool:
        """Uses the retraction check with the live motor position readback."""
        latest_motor_positions = await self.current_motor_positions()
        return (
            self.would_be_fully_retracted_at(
                hypothetical_motor_positions=latest_motor_positions
            )
        )


# Note: Science requirement is that when no attenuator team can take on a demand,
# the correct reaction (canonically) is to retract all absorbers.
# This is achieved without fuss using a Backstop Team class
# Even though it does not feature any physical attenuators,
# it does play an equivalent logical role to the physically realised teams.

class WedgeOnlyTeam(_BaseAttenuatorTeam):

    def __init__(self, *, team_wedge: LogicalWedge):
        self.wedge = team_wedge

    async def current_motor_positions(self) -> AttenuatorMotorPositions:
        return await self.wedge.current_motor_position()

    async def is_validly_positioned(self) -> bool:
        return await self.wedge.is_validly_positioned()

    def would_be_fully_retracted_at(self, *, hypothetical_motor_positions: AttenuatorMotorPositions) -> bool:
        return self.wedge.is_retracted_at(hypothetical_motor_positions=hypothetical_motor_positions)

    def can_accommodate(self, attenuation_demand_bn: float, *, energy_kev: float) -> bool:
        return self.wedge.can_accommodate(attenuation_demand_bn=attenuation_demand_bn, energy_kev=energy_kev)

    def merge_in_retraction_motor_positions(self, *, other_motor_positions: AttenuatorMotorPositions | None = None) -> AttenuatorMotorPositions:
        return self.wedge.merge_in_retraction_motor_position(other_motor_positions=other_motor_positions)

    def predict_attenuation_at(self, *, energy_kev: float, hypothetical_motor_positions: AttenuatorMotorPositions) -> float:
        return (
            self.wedge.predict_attenuation_at(
                energy_kev=energy_kev,
                hypothetical_motor_positions=hypothetical_motor_positions
            )
        )


class WedgeWheelTeam(_BaseAttenuatorTeam):

    def __init__(self,
                 *,
                 team_wedge: LogicalWedge,
                 team_wheel: LogicalWheel):
        self.wedge = team_wedge
        self.wheel = team_wheel
        self.attenuators: Final[frozenset[RetractableAttenuation]] = (
            frozenset([self.wedge, self.wheel])
        )

    async def current_motor_positions(self) -> AttenuatorMotorPositions:
        return (
            await self.wheel.current_index_position()
            | await self.wedge.current_motor_position()
        )

    async def is_validly_positioned(self) -> bool:
        return (
            await self.wedge.is_validly_positioned()
            and await self.wheel.is_validly_positioned()
        )

    def would_be_fully_retracted_at(self, *, hypothetical_motor_positions: AttenuatorMotorPositions) -> bool:
        return all(
            retractable.is_retracted_at(
                hypothetical_motor_positions=hypothetical_motor_positions
            )
            for retractable in self.attenuators
        )

    def can_accommodate(self, attenuation_demand_bn: float, *, energy_kev: float) -> bool:
        return (
            # Since the wheel MUST provide an empty slot,
            # this only depends on the wedge fulcrum condition
            self.wedge.can_accommodate(
                attenuation_demand_bn=attenuation_demand_bn,
                energy_kev=energy_kev
            )
        )

    def merge_in_retraction_motor_positions(
        self, *, other_motor_positions: AttenuatorMotorPositions | None = None
    ) -> AttenuatorMotorPositions:
        return self.wheel.merge_in_empty_slot_reserved_indexed_position(
            other_positions=(
                self.wedge.merge_in_retraction_motor_position(
                    other_motor_positions=other_motor_positions
                )
            )
        )

    def predict_attenuation_at(self, *, energy_kev: float, hypothetical_motor_positions: AttenuatorMotorPositions) -> float:
        return sum(
            [
                a.predict_attenuation_at(
                    energy_kev=energy_kev,
                    hypothetical_motor_positions=hypothetical_motor_positions
                )
                for a in self.attenuators
            ]
        )


@final
class BackstopLogicalTeam(_BaseAttenuatorTeam):
    """Logical catch all, use of which sees all absorbers retracted."""

    async def current_motor_positions(self) -> AttenuatorMotorPositions:
        return AttenuatorMotorPositions()

    async def is_retracted(self) -> bool:
        return True

    async def is_validly_positioned(self) -> bool:
        return True

    def can_accommodate(
        self, attenuation_demand_bn: float, *, energy_kev: float
    ) -> bool:
        return True

    def would_be_fully_retracted_at(
        self, *, hypothetical_motor_positions: AttenuatorMotorPositions
    ) -> bool:
        return True

    def merge_in_retraction_motor_positions(
        self, *, other_motor_positions: AttenuatorMotorPositions | None = None
    ) -> AttenuatorMotorPositions:
        return (
            other_motor_positions
            if other_motor_positions
            else AttenuatorMotorPositions()
        )

    def predict_attenuation_at(
        self,
        *,
        energy_kev: float,
        hypothetical_motor_positions: AttenuatorMotorPositions,
    ) -> float:
        return CANONICAL_NON_ABSORPTION

    def solve_swiftest_motor_shift(
        self,
        attenuation_demand_bn: float,
        *,
        energy_kev: float,
        starting_positions: AttenuatorMotorPositions,
    ) -> AttenuatorMotorPositions:
        return AttenuatorMotorPositions()
