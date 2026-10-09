
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
    PermittedKeyStr,
)
from dodal.devices.beamlines.i19.transmission.retractable_attenuation import (
    LogicalWedge,
)


class _BaseWedge(LogicalWedge):

    def __init__(self, *, wedge_identifier: PermittedKeyStr):
        self._identifier = wedge_identifier

    # Unimplemented abstract methods - to be covered in child classes

    async def _read_current_motor_position(self) -> float: ...

    def _predict_attenuation_at_position(self, *, energy_kev:float, position: float) -> float: ...

    def retracted_position(self) -> AttenuatorMotorPositions: ...

    def can_accommodate(
        self, attenuation_demand_bn: float, *, energy_kev: float
    ) -> bool: ...

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

    # Implemented async API methods ( defined in Protocol LogicalWedge )

    async def current_motor_position(self) -> AttenuatorMotorPositions:
        latest_position = await self._read_current_motor_position()
        return (
            self._wrap_position_in_attenuator_motor_format(
                a_given_position=latest_position
            )
        )

    def merge_in_retraction_motor_position(self, *, other_motor_positions: AttenuatorMotorPositions | None) -> AttenuatorMotorPositions:
        return self.retracted_position() | other_motor_positions


    def _wrap_position_in_attenuator_motor_format(self, *, a_given_position: float) -> AttenuatorMotorPositions:
        return AttenuatorMotorPositions(
            continuous_positions={self._identifier: a_given_position},
        )
