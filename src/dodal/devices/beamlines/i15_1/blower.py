from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import RobotLoadDevicesConfiguration
from ophyd_async.core import derived_signal_rw
from ophyd_async.epics.motor import Motor

XPDF_PARAMETERS_FILEPATH = "/dls_sw/i15-1/software/gda_var/xpdfLocalParameters.xml"


class Blower(Motor):
    def __init__(self, prefix: str, config_client: ConfigClient):
        self.config = config_client.get_file_contents(
            XPDF_PARAMETERS_FILEPATH,
            desired_return_type=RobotLoadDevicesConfiguration,
            force_parser=RobotLoadDevicesConfiguration.from_xpdf_parameters,
        ).blower
        self.in_safe_position = derived_signal_rw(
            self._is_in_safe_position,
            self._set_to_safe_position,
            current_position=self,
        )
        super().__init__(prefix)

    def _is_in_safe_position(self, current_position) -> bool:
        return current_position == self.config.safe_position

    async def _set_to_safe_position(self, value: bool = True):
        if not value:
            raise ValueError("Cannot set blower to 'not safe' this way.")
        await self.set(self.config.safe_position)
