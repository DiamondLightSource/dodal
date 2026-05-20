from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r


class DCM(StandardReadable):
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.energy_in_eV = epics_signal_r(float, f"{prefix}Energy")
            self.wavelength_in_a = epics_signal_r(float, f"{prefix}Wavelength")
