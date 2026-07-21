from daq_config_server.client import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)
from ophyd_async.core import derived_signal_rw
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w

from dodal.common.enums import ValveState
from dodal.devices.beamlines.i15_1.safe_or_beam_positioner import SafeOrBeamPositioner


class Blower(SafeOrBeamPositioner):
    """Blows hot air on to the sample, can be moved out of the beam to allow room for
    a robot load. Temperatures are set in C.

    For safety reasons the heater should only be turned on (set to a >0 temperature) if
    the given pneumatic is open to allow airflow.
    """

    def __init__(
        self,
        prefix: str,
        motion_pv: str,
        pneumatic_pv: str,
        config_client: ConfigClient,
        xpdf_parameters_path: str,
    ):
        self._temperature_sp = epics_signal_w(float, f"{prefix}SP")
        self._temperature_rbv = epics_signal_r(float, f"{prefix}PV:RBV")

        with self.add_children_as_readables():
            self.temperature = derived_signal_rw(
                self._get_temperature,
                self._set_temperature,
                temperature_rbv=self._temperature_rbv,
            )

        self._pneumatic = epics_signal_r(ValveState, pneumatic_pv)
        self.ramp_rate_c_per_sec = epics_signal_rw(
            float, f"{prefix}RR", f"{prefix}RR:RBV"
        )

        super().__init__(motion_pv, config_client, xpdf_parameters_path)

    def _get_temperature(self, temperature_rbv: float) -> float:
        return temperature_rbv

    async def _set_temperature(self, temperature: float):
        """Sets the temperature on the blower.

        A negative or 0 temperature will turn the blower off.
        """
        pneumatic_state = await self._pneumatic.get_value()
        if temperature > 0 and pneumatic_state != ValveState.OPEN:
            raise ValueError("Blower cannot be turned on pneumatic is not open")
        self._temperature_sp.set(temperature)

    def get_config(self) -> TemperatureControllerParams:
        return self.get_full_config().blower
