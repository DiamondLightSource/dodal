
from typing import Annotated, Protocol, runtime_checkable

from pydantic import Field

from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)

# Combined "nominal" X-ray transmission of attenuators
# where "nominal" means ignoring absorption of the gas
# - i.e. in practice asking for 1.0 is an optimism everyone "just" implicitly indulges
Transmission = Annotated[
    float, Field(gt=0.0, le=1.0)
]  # Tx as fraction ( rather than % )


@runtime_checkable
class TransmissionAPI(Protocol):

    async def drive_transmission_to(
        self,
        *,
        transmission_demand: Transmission,
        energy_kev: float,
        starting_positions: AttenuatorMotorPositions,
    ) -> Transmission: ...

    async def read_current_system_transmission(
        self, *, energy_kev: float
    ) -> Transmission: ...

    async def read_current_motor_positions(self) -> AttenuatorMotorPositions: ...

    def predict_transmission_at(
        self, *, energy_kev: float, motor_positions: AttenuatorMotorPositions
    ) -> Transmission: ...

    def solve_for_swiftest_motor_shift(
        self,
        *,
        transmission_demand: Transmission,
        energy_kev: float,
        starting_positions: AttenuatorMotorPositions,
    ) -> AttenuatorMotorPositions: ...
