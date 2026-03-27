from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
    TemperatureControllersConfig,
)

from dodal.devices.beamlines.i15_1.temperature_controller import TemperatureController


class Blower(TemperatureController):
    def __init__(
        self, prefix: str, config_client: ConfigClient, xpdf_parameters_path: str
    ):
        self.config_client = config_client
        self.xpdf_parameters_path = xpdf_parameters_path
        super().__init__(prefix)

    def get_config(self) -> TemperatureControllerParams:
        return self.config_client.get_file_contents(
            self.xpdf_parameters_path,
            desired_return_type=TemperatureControllersConfig,
            force_parser=TemperatureControllersConfig.from_xpdf_parameters,
        ).blower

    @property
    def _safe_position(self) -> float:
        return self.get_config().safe_position

    @property
    def _beam_position(self) -> float:
        return self.get_config().beam_position
