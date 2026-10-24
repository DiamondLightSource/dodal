

from abc import ABC, abstractmethod
from typing import Protocol

from dodal.devices.beamlines.i19.transmission.internal_protocols import (
    SupportsForecasting,
)

from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.energy_specific_attenuation import (
    EnergySpecificAttenuation,
)


class SupportsForecasting(Protocol):

    def is_an_energy_appropriate_state(self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions) -> bool: ...

    def is_a_fully_retracted_state(self, *, attenuator_motor_positions: AttenuatorMotorPositions) -> bool: ...

    def predict_attenuation_bn(self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions) -> EnergySpecificAttenuation: ...



class BaseForecasting(SupportsForecasting, ABC):

    @abstractmethod
    def is_an_energy_appropriate_state(self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions) -> bool:
        ...

    @abstractmethod
    def is_a_fully_retracted_state(self, *, attenuator_motor_positions: AttenuatorMotorPositions) -> bool:
        ...

    @abstractmethod
    def predict_attenuation_bn(self, *, energy_kev: float, attenuator_motor_positions: AttenuatorMotorPositions) -> EnergySpecificAttenuation: ...








