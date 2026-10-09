from typing import Annotated, Protocol, runtime_checkable

from pydantic import Field, validate_call

from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.retractable_attenuation import (
    RetractableAttenuation,
)

StrictPositiveFloat = Annotated[float, Field(strict=True, gt=0)]

# Combined "nominal" X-ray transmission of attenuators
# where "nominal" means ignoring absorption of the gas
# - i.e. in practice asking for 1.0 is an optimism everyone "just" implicitly indulges
Transmission = Annotated[
    StrictPositiveFloat, Field(le=1.0)
]  # Tx as fraction ( rather than % )


@runtime_checkable
class TransmissionAPI(Protocol):
    async def drive_transmission_to(
        self,
        *,
        transmission_demand: Transmission,
        energy_kev: StrictPositiveFloat,
        starting_positions: AttenuatorMotorPositions,
    ) -> Transmission: ...

    async def read_transmission(
        self, *, energy_kev: StrictPositiveFloat
    ) -> Transmission: ...

    async def read_current_motor_positions(self) -> AttenuatorMotorPositions: ...

    def predict_transmission_at(
        self,
        *,
        energy_kev: StrictPositiveFloat,
        motor_positions: AttenuatorMotorPositions,
    ) -> Transmission: ...

    def solve_for_swiftest_motor_shift(
        self,
        *,
        transmission_demand: Transmission,
        energy_kev: StrictPositiveFloat,
        starting_positions: AttenuatorMotorPositions,
    ) -> AttenuatorMotorPositions: ...


@runtime_checkable
class AttenuatorTeam(RetractableAttenuation, Protocol):
    async def current_motor_positions(self) -> AttenuatorMotorPositions: ...

    def can_accommodate(
        self, attenuation_demand_bn: float, *, energy_kev: float
    ) -> bool: ...

    def merge_in_retraction_motor_positions(
        self, *, other_motor_positions: AttenuatorMotorPositions | None
    ) -> AttenuatorMotorPositions: ...

    @validate_call
    def solve_swiftest_motor_shift(
        self,
        attenuation_demand_bn: float,
        *,
        energy_kev: float,
        starting_positions: AttenuatorMotorPositions,
    ) -> AttenuatorMotorPositions: ...


class IneligibleMaterialError(Exception): ...
