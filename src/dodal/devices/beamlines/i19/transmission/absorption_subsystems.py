from typing import Protocol

from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorPositions,
)
from dodal.devices.beamlines.i19.transmission.absorber_wheel import (
    AbsorberWheel,
)
from dodal.devices.beamlines.i19.transmission.absorption_contributer import (
    AbsorptionContributer,
)


class SubSystem(Protocol):
    def predict_closest_matching_absorptions(
        self, *, energy_kev: float, demand_bn: float
    ) -> dict[str, float]: ...

    def predict_fastest_matching_motor_positions(
        self, *, energy_kev: float, demand_bn: float
    ) -> AttenuatorMotorPositions: ...


class PrimaryAbsorption(AbsorptionContributer):
    def __init__(self, *, wedge, filter_wheel):
        self.wedge: AbsorptionContributer = wedge
        self.wheel: AbsorberWheel = filter_wheel

    def _collate_motor_positions(
        self, *, wheel_index: int, wedge_position: float
    ) -> AttenuatorMotorPositions:
        wheel_pos = self.wheel.id
        return

    def is_suitable_for_energy(self, *, xray_energy_kev: float) -> bool:
        return self.wedge.is_suitable_for_energy(xray_energy_kev=xray_energy_kev)

    def is_feasible(self, *, xray_energy_kev: float, demand_bn: float) -> bool:
        return self.wedge.is_feasible(
            xray_energy_kev=xray_energy_kev, demand_bn=demand_bn
        )

    def predict_closest_matching_absorptions(
        self, *, xray_energy_kev: float, demand_bn: float
    ) -> dict[str, float]:
        # Map slot index vs residual demand (in Bn) left over after each available wheel filter
        wheel_residual_register: dict[int, float] = (
            self.wheel.residuals_for_all_slots_able_to_contribute(
                xray_energy_kev=xray_energy_kev, demand_bn=demand_bn
            )
        )
        # remove filters that take so much out of the demand
        # - there's too little demand left for the wedge to cope
        # ( yes it's counterintuitive,
        # - we usually imagine something is inadequate for a demand,
        #  but here the issue would be if too much absorption happens,
        # because the wedge cannot do less,
        # - except for getting out of the way completely )
        wedge_compatible_options = {
            slot_index: residual_bn
            for slot_index, residual_bn in wheel_residual_register.items()
            if self.is_feasible(xray_energy_kev=xray_energy_kev, demand_bn=residual_bn)
        }
        ...
