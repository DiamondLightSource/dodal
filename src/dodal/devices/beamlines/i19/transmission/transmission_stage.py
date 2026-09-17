from collections.abc import Callable

from dodal.devices.beamlines.i19.transmission.transmission_solutions import (
    AttenuationSolution,
    AttenuatorSubsystem,
    BaseAttenuatorSubsystem,
    TransmissionMatch,
)
from ophyd_async.core._device import Device

from dodal.common.general_maths.transmission_interconversion import (
    attenuation_from_transmission,
    transmission_from_attenutation,
)


class TransmissionStage(Device):
    def __init__(self, *, name: str, beamline_prefix: str, rbv_infixes: dict[str, str]):
        self.delegate: AttenuatorSubsystem = BaseAttenuatorSubsystem()

    def predict_transmission(self, *, energy_kev: float) -> float:
        _attenuation_bn = self.delegate.predict_attenuation_bn(energy_kev=energy_kev)
        return transmission_from_attenutation(attenuation_bn=_attenuation_bn)

    def closest_match_transmission(
        self, *, energy_kev: float, target_transmission: float
    ) -> TransmissionMatch:
        _target_attenuation_bn = attenuation_from_transmission(
            transmission_as_fraction=target_transmission
        )
        _attenuation_solution = self.delegate.predict_closest_solution(
            energy_kev=energy_kev, attenuation_target=_target_attenuation_bn
        )
        return self._recast_attenuation_solution_as_transmission(
            attenuation_solution=_attenuation_solution,
            conversion=transmission_from_attenutation,
        )

    def _recast_attenuation_solution_as_transmission(
        self,
        *,
        attenuation_solution: AttenuationSolution,
        conversion: Callable[[float], float],
    ) -> TransmissionMatch:
        _target_transmission = conversion(attenuation_solution.target)
        _closest_match_transmission = conversion(attenuation_solution.closest_match)
        return TransmissionMatch(
            energy_kev=attenuation_solution.energy_kev,
            target=_target_transmission,
            closest_match=_closest_match_transmission,
            position_solution=attenuation_solution.position_solution,
        )
