from dodal.common.general_maths.absorbers import EnergyDependentAbsorber
from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)


class AbsorptionContributer(EnergyDependentAbsorber):
    # Abstract API methods

    def predict_absorption_at_given_energy(self, *, xray_energy_kev: float) -> float:
        """Predict the absorption at the given energy at the present motor positions."""
        ...

    # Concrete API methods below
    # API methods that are almost universal ( empty slot overrides them )

    def is_feasible(self, *, xray_energy_kev: float, demand_bn: float) -> bool:
        """If the absorption element(s) can be used at the input energy, without blowing the demand budget."""
        return self.is_suitable_for_energy(
            xray_energy_kev=xray_energy_kev
        ) and not self._absorption_exceeds_demand(
            xray_energy_kev=xray_energy_kev, demand_bn=demand_bn
        )

    def predict_residual_demand(
        self, *, xray_energy_kev: float, demand_bn: float
    ) -> float:
        """What the residual would be after this system was used to absorb."""
        return demand_bn - self.predict_absorption_at_given_energy(
            xray_energy_kev=xray_energy_kev
        )

    def _absorption_exceeds_demand(
        self, *, xray_energy_kev: float, demand_bn: float
    ) -> bool:
        return (
            self.predict_residual_demand(
                xray_energy_kev=xray_energy_kev, demand_bn=demand_bn
            )
            < CANONICAL_NON_ABSORPTION
        )


class AbsenceFromBeam(AbsorptionContributer):
    def is_suitable_for_energy(self, *, xray_energy_kev: float) -> bool:
        return True

    def is_feasible(self, *, xray_energy_kev: float, demand_bn: float):
        return True

    def predict_residual_demand(
        self, *, xray_energy_kev: float, demand_bn: float
    ) -> float:
        return demand_bn

    def predict_absorption_at_given_energy(self, *, xray_energy_kev: float) -> float:
        return CANONICAL_NON_ABSORPTION
