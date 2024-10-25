from ophyd_async.core import Device

from dodal.devices.current_amplifiers import Femto


class RasorFemto(Device):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.ca1 = Femto(prefix + "-01:")
        self.ca2 = Femto(prefix + "-02:")
        self.ca3 = Femto(prefix + "-03:")

        super().__init__(name)
