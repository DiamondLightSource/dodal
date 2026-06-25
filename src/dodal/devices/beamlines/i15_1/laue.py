from daq_config_server import ConfigClient
from daq_config_server.models.i15_1 import XpdfCrystalLookupTable
from ophyd_async.core import StandardReadable, StandardReadableFormat, derived_signal_r
from ophyd_async.epics.motor import Motor


class LaueMonochrometer(StandardReadable):
    def __init__(
        self,
        prefix: str,
        config_client: ConfigClient,
        crystal_lut_path: str,
        name: str = "",
    ):
        self.bend = Motor(prefix + "BENDER")
        self.bragg = Motor(prefix + "PITCH")
        self.roll = Motor(prefix + "ROLL")
        self.yaw = Motor(prefix + "YAW")
        self.y = Motor(prefix + "Y")

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.energy_kev = derived_signal_r(self._get_energy, y=self.y)

        self._config_client = config_client
        self._crystal_lut_path = crystal_lut_path

        super().__init__(name)

    def _get_xtal_config(self) -> XpdfCrystalLookupTable:
        return self._config_client.get_file_contents(
            self._crystal_lut_path, XpdfCrystalLookupTable
        )

    def _get_energy(self, y: float) -> float:
        xtal_lut = self._get_xtal_config()
        return xtal_lut.get_energy(y)
