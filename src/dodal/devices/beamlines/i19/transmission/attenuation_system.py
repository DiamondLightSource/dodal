import asyncio
import operator
from functools import reduce

from ophyd_async.core import Device

from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.team import BaseTeam, Team


class AttenuationSystem(Device):
    def __init__(self, *attenuating_subsystems: Team) -> None:
        self.otherwise_all_out: Team = BaseTeam()  # if all else fails remove all attenuators
        self.teams: tuple[Team, ...] = (*attenuating_subsystems,)


    async def get_current_motor_positions(self) -> AttenuatorMotorPositions:
        async with asyncio.TaskGroup() as task_grp:
            read_out_positions_tasks = [
                task_grp.create_task(
                    t.current_motor_positions()
                )
                for t in self.teams
            ]
        team_positions_reported = [task.result() for task in read_out_positions_tasks]
        if not team_positions_reported:
            raise RuntimeError("No reported motor positions")
        else:
            # concatenate/merge all individual motor positions into one AMP using reduce
            return reduce(operator.or_, team_positions_reported)


    async def read_system_attenuation_bn(
        self, *, energy_kev: float, strict:bool=True
    ) -> float:
        cmp = await self.get_current_motor_positions()
        return self.predict_attenuation_bn_at(energy_kev=energy_kev, motor_positions=cmp, strict=strict)


    def predict_attenuation_bn_at(
        self, *, energy_kev: float, motor_positions: AttenuatorMotorPositions, strict:bool=True
    ) -> float:
        # prepare parallel checks - of retraction - on each subsystem "Attenuator Team"
        # filter out inactive teams (which have - by definition - retracted their attenuators)
        hypothetically_active_teams: list[Team] = (
            self._find_unretracted_teams_if_motors_were_at(motor_positions=motor_positions)
        )

        if strict and len(hypothetically_active_teams) > 1:
            # Flag illegal state whenever more than one team has attenuators in play
            raise RuntimeError(f"Illegal state: More than one active attenuator subsystem for positions {motor_positions}.")

        if not hypothetically_active_teams:
            return CANONICAL_NON_ABSORPTION

        attenuation_contributions: list[float] = [
            team.predict_attenuation_at(energy_kev=energy_kev,
                                        hypothetical_motor_positions=motor_positions)
            for team in self.teams
        ]
        return reduce(operator.add, attenuation_contributions)


    def solve_for_swiftest_motor_shift(
        self,
        *,
        attenuation_demand_bn: float,
        energy_kev: float,
        starting_positions: AttenuatorMotorPositions,
    ) -> AttenuatorMotorPositions:
        suitable_subsystem: Team | None = None
        positions = AttenuatorMotorPositions()
        for team in self.teams:
            if suitable_subsystem is None and team.is_suitable_for(
                attenuation_demand_bn, energy_kev=energy_kev
            ):
                positions |= team.solve_swiftest_motor_shift(
                    attenuation_demand_bn=attenuation_demand_bn,
                    energy_kev=energy_kev,
                    starting_positions=starting_positions,
                )
                suitable_subsystem = team
            else:
                positions = team.merge_in_retraction_motor_positions(
                    other_motor_positions=positions
                )
        return positions


    def _find_first_suitable_subsystem(self, *, attenuation_demand_bn: float, energy_kev: float):
        return next(
            (
                team for team in self.teams
                if team.is_suitable_for(attenuation_demand_bn, energy_kev=energy_kev)
            ),
            self.otherwise_all_out
        )


    def _find_unretracted_teams_if_motors_were_at(self, *, motor_positions: AttenuatorMotorPositions) -> list[Team]:
        return [
            team for team in self.teams
            if not team.is_retracted_at(hypothetical_motor_positions=motor_positions)
        ]
