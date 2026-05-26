from daq_config_server import ConfigClient
from daq_config_server.models.i15_1 import XpdfCrystalLookupTable
from ophyd_async.core import StandardReadable, derived_signal_r
from ophyd_async.epics.motor import Motor


class LaueMonochrometer(StandardReadable):
    def __init__(
        self,
        prefix: str,
        config_client: ConfigClient,
        crystal_lut_path: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.bend = Motor(prefix + "BENDER")
            self.bragg = Motor(prefix + "PITCH")
            self.roll = Motor(prefix + "ROLL")
            self.yaw = Motor(prefix + "YAW")
            self.y = Motor(prefix + "Y")
            self.energy_kev = derived_signal_r(self._get_energy, y=self.y)
            self.config_client = config_client
            self.crystal_lut_path = crystal_lut_path

        super().__init__(name)

    def _get_xtal_config(self) -> XpdfCrystalLookupTable:
        return self.config_client.get_file_contents(
            self.crystal_lut_path,
            XpdfCrystalLookupTable,
            # Remove once new config server is released + deployed
            force_parser=XpdfCrystalLookupTable.from_contents,
        )

    def _get_energy(self, y: float) -> float:
        xtal_lut = self._get_xtal_config()
        return xtal_lut.get_energy(y)
