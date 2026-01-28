from ophyd_async.core import Device

from dodal.devices.current_amplifiers import (
    SR570,
)


class ElectromagnetSR570(Device):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.ca1 = SR570(
            prefix + "-08:",
        )
        self.ca2 = SR570(
            prefix + "-09:",
        )
        super().__init__(name)
