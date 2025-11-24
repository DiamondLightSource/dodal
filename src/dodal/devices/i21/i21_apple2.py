from dodal.devices.i21.enums import Grating
from dodal.devices.util.lookup_tables_apple2 import (
    EnergyMotorLookup,
    Pol,
)


class I21EnergyMotorLookup(EnergyMotorLookup):
    """Add an helper function to get the correct grading from lookup table"""

    def get_grating_from_energy(self, energy: float, pol: Pol) -> Grating:
        if (
            energy < self.lookup_tables.gap.root[pol].limit.minimum
            or energy > self.lookup_tables.gap.root[pol].limit.maximum
        ):
            raise ValueError(
                "Demanding energy must lie between"
                + f" {self.lookup_tables.gap.root[pol].limit.minimum}"
                + f" and {self.lookup_tables.gap.root[pol].limit.maximum} eV!"
            )
        else:
            for energy_range in self.lookup_tables.gap.root[pol].energies.root.values():
                if energy >= energy_range.low and energy < energy_range.high:
                    if energy_range.grading is not None:
                        return Grating[energy_range.grading]
        raise ValueError("Grading undefine in lookup table")
