from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)

from dodal.devices.beamlines.i15_1.temperature_controller import SafeOrBeamPositioner


class Cobra(SafeOrBeamPositioner):
    def get_config(self) -> TemperatureControllerParams:
        return self.get_full_config().cobra
