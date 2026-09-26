from ophyd_async.core import Device
from pydantic import validate_call

from dodal.common.general_maths.transmission_interconversion import (
    attenuation_from_transmission,
    transmission_from_attenuation,
)
from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorSquad,
)
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.attenuation_system import (
    AttenuationSystem,
)
from dodal.devices.beamlines.i19.transmission.transmission_api import Transmission


class TransmissionStage(Device):
    def __init__(
        self,
        *,
        tx_stage_name: str,
        motors_squad: AttenuatorMotorSquad,
        attenuation_system: AttenuationSystem,
    ) -> None:
        self.access_controlled_motors = motors_squad
        self.internal_system = attenuation_system
        super().__init__(name=tx_stage_name)

    @validate_call
    async def drive_transmission_to(
        self,
        *,
        transmission_demand: Transmission,
        energy_kev: float,
        starting_positions: AttenuatorMotorPositions,
    ) -> Transmission:

        _motors_demand: AttenuatorMotorPositions = self.solve_for_swiftest_motor_shift(
            transmission_demand=transmission_demand,
            energy_kev=energy_kev,
            starting_positions=starting_positions,
        )

        await self.access_controlled_motors.set(value=_motors_demand)
        _motors_result = await self.read_current_motor_positions()

        return self.predict_transmission_at(
            energy_kev=energy_kev, motor_positions=_motors_result
        )

    @validate_call
    async def read_current_system_transmission(
        self, *, energy_kev: float
    ) -> Transmission:
        attn_bn: float = await self.internal_system.read_system_attenuation_bn(
            energy_kev=energy_kev
        )
        return transmission_from_attenuation(attenuation_bn=attn_bn)


    async def read_current_motor_positions(self) -> AttenuatorMotorPositions:
        return await self.internal_system.get_current_motor_positions()


    @validate_call
    def predict_transmission_at(
        self, *, energy_kev: float, motor_positions: AttenuatorMotorPositions
    ) -> Transmission:
        attn_bn: float = self.internal_system.predict_attenuation_bn_at(
            energy_kev=energy_kev, motor_positions=motor_positions
        )
        return transmission_from_attenuation(attenuation_bn=attn_bn)


    @validate_call
    def solve_for_swiftest_motor_shift(
        self,
        *,
        transmission_demand: Transmission,
        energy_kev: float,
        starting_positions: AttenuatorMotorPositions,
    ) -> AttenuatorMotorPositions:
        """Finds motor position solution to meet transmission demand in quickest (motor) time.

        Note:
            The requirement to minimise motor movement times,
            binds the solution to the present motor positions -
            hence the method is asynchronous as it must first
            read the starting motor disposition.
        """
        attenuation_demand_bn: float = attenuation_from_transmission(
            transmission_as_fraction=transmission_demand
        )
        return self.internal_system.solve_for_swiftest_motor_shift(
            attenuation_demand_bn=attenuation_demand_bn,
            energy_kev=energy_kev,
            starting_positions=starting_positions,
        )
