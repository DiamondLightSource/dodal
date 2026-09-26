from typing import Protocol

from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)


class Team(Protocol):

    async def current_motor_positions(self) -> AttenuatorMotorPositions: ...

    async def get_attenuation_bn(self, *, energy_kev: float) -> float: ...

    async def is_retracted(self) -> bool: ...

    async def is_validly_positioned(self) -> bool: ...

    def is_retracted_at(
        self, *, hypothetical_motor_positions: AttenuatorMotorPositions
    ) -> bool: ...

    def is_suitable_for(
        self, attenuation_demand_bn: float, *, energy_kev: float
    ) -> float: ...

    def merge_in_retraction_motor_positions(
        self, *, other_motor_positions: AttenuatorMotorPositions | None
    ) -> AttenuatorMotorPositions: ...

    def predict_attenuation_at(
        self,
        *,
        energy_kev: float,
        hypothetical_motor_positions: AttenuatorMotorPositions,
    ) -> float: ...

    def solve_swiftest_motor_shift(
        self,
        attenuation_demand_bn: float,
        *,
        energy_kev: float,
        starting_positions: AttenuatorMotorPositions,
    ) -> AttenuatorMotorPositions: ...


class BaseTeam:

    async def current_motor_positions(self) -> AttenuatorMotorPositions:
        return AttenuatorMotorPositions()


    async def get_attenuation_bn(self, *, energy_kev: float) -> float:
        motor_positions = await self.current_motor_positions()
        return (
            self.predict_attenuation_at(energy_kev=energy_kev,
                                        hypothetical_motor_positions=motor_positions)
        )


    async def is_retracted(self) -> bool:
        return True


    async def is_validly_positioned(self) -> bool:
        return True


    def is_retracted_at(self, *, hypothetical_motor_positions: AttenuatorMotorPositions) -> bool:
        return True


    def is_suitable_for(
        self, attenuation_demand_bn: float, *, energy_kev: float
    ) -> float:
        return True


    def merge_in_retraction_motor_positions(self, *, other_motor_positions: AttenuatorMotorPositions | None=None) -> AttenuatorMotorPositions:
        return other_motor_positions if other_motor_positions else AttenuatorMotorPositions()


    def predict_attenuation_at(self, *, energy_kev: float, hypothetical_motor_positions: AttenuatorMotorPositions) -> float:
        return CANONICAL_NON_ABSORPTION


    def solve_swiftest_motor_shift(
        self, attenuation_demand_bn: float, *, energy_kev: float, starting_positions: AttenuatorMotorPositions,
    ) -> AttenuatorMotorPositions:
        return AttenuatorMotorPositions()
