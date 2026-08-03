from pydantic import (
    BaseModel,
    ConfigDict,
    StrictFloat,
)
from pydantic.dataclasses import dataclass

from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorPositions,
)


class AttenuationRequest(BaseModel):
    """Pairing off, of an x-ray energy and requested attenuation.

    Features system friendly capacity to calculate remainder requests, based on reductions from allocated absorption.

    Args:
        xray_energy_kev: The x-ray energy relevant for the requested attenuation.
        target_bn: The remaining attenuation from the system budget that we want to burn.
    """

    xray_energy_kev: StrictFloat
    target_bn: StrictFloat

    model_config = ConfigDict(frozen=True)

    def _calculate_residual_bn(
        self,
        *,
        satisfied_attenuation_bn: StrictFloat,
    ) -> float:
        """Internal method to calculate burn down of attenuation budget in request.

        Args:
            satisfied_attenuation_bn:  The latest reduction in the unsatisfied request which is about to be met.

        Returns:
            the reduced attenuation demand, reduced by the satisfied portion.
        """
        return self.target_bn - satisfied_attenuation_bn

    def calculate_remaining_request(
        self, *, satisfied_attenuation_bn: StrictFloat
    ) -> "AttenuationRequest":
        """Generates new request with the remaining (unmet) attenuation demand, given a certain amount has already been satisfied.

        Args:
            satisfied_attenuation_bn: The amount of attenuation (Barnett units) already covered by absorbers considered.

        Return:
            Amortized version of the original request, with only the unmet portion of the original absorption budget.

        Raises:
            Will raise Validation error if the satisfied attenuation exceeds the original budget.
        """
        _residual_bn = self._calculate_residual_bn(
            satisfied_attenuation_bn=satisfied_attenuation_bn
        )
        return AttenuationRequest(
            xray_energy_kev=self.xray_energy_kev, target_bn=_residual_bn
        )


@dataclass(kw_only=True, frozen=True)
class AttenuationMatch:
    request: AttenuationRequest
    closest_attenuation_bn: StrictFloat
    implementation: AttenuatorMotorPositions


class AttenuatorSubsystem(Attenuator):
    def predict_efficient_match(self, request: AttenuationRequest) -> AttenuationMatch:
        """Reports nearest reachable attenuation of the subsystem (in Barnett Units), at input energy.

        The calculation is based on restrictions imposed on,
        permitted motor positions,
        and suitability of absorbers for particular energy ranges.

        Args:
            request: The requested attenuation and energy

        Returns:
            Summary of the nearest achievable solution.
        """
        ...
