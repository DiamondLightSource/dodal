from ophyd_async.core import Device
from ophyd_async.core._device import DeviceConnector

from dodal.devices.temperture_controller import (
    LAKESHORE336_HEATER_SETTING,
    LAKESHORE336_PID_INPUT_CHANNEL,
    LAKESHORE336_PID_MODE,
    Lakeshore336,
)


class I06DDTemperatureController(Device):
    def __init__(
        self, prefix: str, name: str = "", connector: DeviceConnector | None = None
    ) -> None:
        """Two lakeshore controllers for heating and cooling insert"""
        self.cooling_insert = Lakeshore336(
            prefix=f"{prefix}-EA-TCTRL-02:",
            no_channels=4,
            heater_setting=LAKESHORE336_HEATER_SETTING,
            pid_mode=LAKESHORE336_PID_MODE,
            input_channel_type=LAKESHORE336_PID_INPUT_CHANNEL,
        )
        self.heating_insert = Lakeshore336(
            prefix=f"{prefix}-EA-TCTRL-03:",
            no_channels=4,
            heater_setting=LAKESHORE336_HEATER_SETTING,
            pid_mode=LAKESHORE336_PID_MODE,
            input_channel_type=LAKESHORE336_PID_INPUT_CHANNEL,
        )

        super().__init__(name, connector)
