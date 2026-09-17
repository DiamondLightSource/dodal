from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Concatenate, Final, ParamSpec, Protocol, TypeVar, final

from dodal.common.general_maths.absorbers import FixedDepth, VariableDepth
from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.system_absorber_models import (
    SpecifiedWedgeModel,
)

ALL_OUT: Final[AttenuatorMotorPositions] = AttenuatorMotorPositions(
    continuous_positions={}, discrete_indices={}
)

Q = TypeVar("Q", int, float)  # read out of either motor position or wheel index
S = ParamSpec("S")
T = TypeVar("T", VariableDepth, FixedDepth)

class RetractableAttenuator(Protocol[Q]):
    def is_retracted_at_position(self, *, position: Q) -> bool: ...

    def readout(self) -> Q: ...


A = TypeVar("A", bound=RetractableAttenuator[Any])

# Decorator for absorption calculations to bypass irrelevant calculations,
# when the absorber is not even in the x-ray beam.
def transparent_if_retracted(
    attenuation_calc: Callable[Concatenate[A, Q, S], float],
) -> Callable[Concatenate[A, S], float]:
    """A retracted absorber should immediately report optical transparency."""

    @wraps(attenuation_calc)
    def calculation_wrapper(self: A, *args: S.args, **kwargs: S.kwargs) -> float:
        """Skip irrelevant physis calculations when absorber retracted."""
        _present_position: Q = self.readout()
        return (
            CANONICAL_NON_ABSORPTION
            if self.is_retracted_at_position(position=_present_position)
            else attenuation_calc(self, _present_position, *args, **kwargs)
        )

    return calculation_wrapper


@dataclass(frozen=True)
class TargetedBestMatch:
    energy_kev: float
    target: float
    closest_match: float
    position_solution: AttenuatorMotorPositions

@final
class TransmissionMatch(TargetedBestMatch): ...

@final
class AttenuationSolution(TargetedBestMatch): ...


class AttenuatorSubsystem(Protocol):
    def fulcrum_attenuation_bn(self, *, energy_kev: float) -> float: ...

    def predict_attenuation_bn(self, *, energy_kev: float) -> float: ...

    def predict_closest_solution(
        self, *, energy_kev: float, attenuation_target: float
    ) -> AttenuationSolution: ...


class BaseAttenuatorSubsystem(ABC):

    @abstractmethod
    def fulcrum_attenuation_bn(self, *, energy_kev: float) -> float: ...

    @abstractmethod
    def predict_attenuation_bn(self, *, energy_kev: float) -> float: ...

    def predict_closest_solution(
        self, *, energy_kev: float, attenuation_target: float
    ) -> AttenuationSolution:
        return AttenuationSolution(
            energy_kev=energy_kev,
            target=attenuation_target,
            closest_match=CANONICAL_NON_ABSORPTION,
            position_solution=ALL_OUT,
        )

    def is_out_of_xray_beam(self) -> bool:
        return True


class OneWedgeSubSystem(BaseAttenuatorSubsystem, RetractableAttenuator[float]):
    def __init__(self, *, specifications: Any, position_readout: Callable[[], float]):
        self.wedge_model = SpecifiedWedgeModel(specifications=specifications)
        self.callable_readout = position_readout

    def fulcrum_attenuation_bn(self, *, energy_kev: float) -> float:
        return self.wedge_model.fulcrum_attenuation_bn(energy_kev=energy_kev)

    def predict_attenuation_bn(self, *, energy_kev: float) -> float:
        return self._predict_attenuation_bn(energy_kev=energy_kev)

    def is_retracted_at_position(self, *, position: float) -> bool:
        return self.wedge_model.is_wedge_out(position)

    def is_out_of_xray_beam(self) -> bool:
        _latest_position = self.readout()
        return self.is_retracted_at_position(position=_latest_position)

    def readout(self) -> float:
        return self.callable_readout()

    @transparent_if_retracted
    def _predict_attenuation_bn(
        self,
        latest_position: float,
        *,
        energy_kev: float,
    ) -> float:
        return self.wedge_model.calculate_absorption_bn(
            xray_energy_kev=energy_kev, motor_position_mm=latest_position
        )
