from typing import Protocol

from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.energy_specific_attenuation import (
    EnergySpecificAttenuation,
)


class AttenuatingSubsystem(Protocol):
    def can_accommodate(self, *, demand: EnergySpecificAttenuation) -> bool: ...


class SupportsForecasting(Protocol):
    def forecast_attenuation(
        self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions
    ) -> float: ...
