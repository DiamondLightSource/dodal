from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)

from dodal.devices.beamlines.i15_1.safe_or_beam_positioner import SafeOrBeamPositioner


class Blower(SafeOrBeamPositioner):
    def get_config(self) -> TemperatureControllerParams:
        return self.get_full_config().blower
