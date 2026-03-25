from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import RobotLoadDevicesConfiguration

from dodal.devices.beamlines.i15_1.motor_with_safe_position import MotorWithSafePosition

XPDF_PARAMETERS_FILEPATH = "/dls_sw/i15-1/software/gda_var/xpdfLocalParameters.xml"


class Cobra(MotorWithSafePosition):
    def __init__(self, prefix: str, config_client: ConfigClient):
        self.config = config_client.get_file_contents(
            XPDF_PARAMETERS_FILEPATH,
            desired_return_type=RobotLoadDevicesConfiguration,
            force_parser=RobotLoadDevicesConfiguration.from_xpdf_parameters,
        ).cobra
        super().__init__(prefix)

    @property
    def _safe_position(self) -> float:
        return self.config.safe_position
