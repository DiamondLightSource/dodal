from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    RobotLoadDeviceConfiguration,
    RobotLoadDevicesConfiguration,
)

from dodal.devices.beamlines.i15_1.blower import XPDF_PARAMETERS_FILEPATH
from dodal.devices.beamlines.i15_1.temperature_controller import TemperatureController


class Cobra(TemperatureController):
    def __init__(self, prefix: str, config_client: ConfigClient):
        self.config_client = config_client
        super().__init__(prefix)

    def get_config(self) -> RobotLoadDeviceConfiguration:
        return self.config_client.get_file_contents(
            XPDF_PARAMETERS_FILEPATH,
            desired_return_type=RobotLoadDevicesConfiguration,
            force_parser=RobotLoadDevicesConfiguration.from_xpdf_parameters,
        ).cobra

    @property
    def _safe_position(self) -> float:
        return self.get_config().safe_position

    @property
    def _beam_position(self) -> float:
        return self.get_config().beam_position
