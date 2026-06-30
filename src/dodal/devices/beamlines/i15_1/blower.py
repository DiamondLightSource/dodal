from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.beamlines.i15_1.safe_or_beam_positioner import SafeOrBeamPositioner


class Blower(SafeOrBeamPositioner):
    def __init__(
        self,
        prefix: str,
        motion_pv: str,
        config_client: ConfigClient,
        xpdf_parameters_path: str,
    ):
        with self.add_children_as_readables():
            self.temperature = epics_signal_rw(float, f"{prefix}PV:RBV", f"{prefix}SP")

        self.ramp_rate = epics_signal_rw(float, f"{prefix}RR", f"{prefix}RR:RBV")

        super().__init__(motion_pv, config_client, xpdf_parameters_path)

    def get_config(self) -> TemperatureControllerParams:
        return self.get_full_config().blower
