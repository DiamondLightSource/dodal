from daq_config_server.client import ConfigServer

from dodal.devices.apple2_undulator import Pol
from dodal.devices.util.lookup_tables_apple2 import (
    EnergyMotorLookup,
    Lookuptable,
    convert_csv_to_lookup,
    make_phase_tables,
)
from dodal.log import LOGGER

ROW_PHASE_MOTOR_TOLERANCE = 0.004
ROW_PHASE_CIRCULAR = 15
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100
DEFAULT_JAW_PHASE_POLY_PARAMS = [1.0 / 7.5, -120.0 / 7.5]
ALPHA_OFFSET = 180
MAXIMUM_MOVE_TIME = 550  # There is no useful movements take longer than this.


J09PhasePoly1dParameters = {
    "LH": [0],
    "LV": [MAXIMUM_ROW_PHASE_MOTOR_POSITION],
    "PC": [ROW_PHASE_CIRCULAR],
    "NC": [ROW_PHASE_CIRCULAR],
    "LH3": [0],
}


class J09EnergyMotorLookup(EnergyMotorLookup):
    """
    Handles lookup tables for I10 Apple2 ID, converting energy and polarisation to gap
     and phase. Fetches and parses lookup tables from a config server, supports dynamic
     updates, and validates input.
    """

    def __init__(
        self,
        lookuptable_dir: str,
        config_client: ConfigServer,
        mode: str = "Mode",
        min_energy: str = "MinEnergy",
        max_energy: str = "MaxEnergy",
        gap_file_name: str = "IDEnergy2GapCalibrations.csv",
        poly_deg: list | None = None,
    ):
        """Initialise the I10EnergyMotorLookup class with lookup table headers provided.

        Parameters
        ----------
        look_up_table_dir:
            The path to look up table.
        source:
            The column name and the name of the source in look up table. e.g. ( "source", "idu")
        config_client:
            The config server client to fetch the look up table.
        mode:
            The column name of the mode in look up table.
        min_energy:
            The column name that contain the maximum energy in look up table.
        max_energy:
            The column name that contain the maximum energy in look up table.
        poly_deg:
            The column names for the parameters for the energy conversion polynomial, starting with the least significant.

        """
        super().__init__(
            lookuptable_dir=lookuptable_dir,
            config_client=config_client,
            mode=mode,
            min_energy=min_energy,
            max_energy=max_energy,
            gap_file_name=gap_file_name,
            phase_file_name=None,
            poly_deg=poly_deg,
        )

    def update_lookuptable(self):
        """
        Update lookup tables from files and validate their format.
        """
        LOGGER.info("Updating lookup dictionary from file.")
        for key, path in self.lookup_table_config.path.__dict__.items():
            if path is not None:
                csv_file = self.config_client.get_file_contents(
                    path, reset_cached_result=True
                )
                self.lookup_tables[key] = convert_csv_to_lookup(
                    file=csv_file,
                    mode=self.lookup_table_config.mode,
                    min_energy=self.lookup_table_config.min_energy,
                    max_energy=self.lookup_table_config.max_energy,
                    poly_deg=self.lookup_table_config.poly_deg,
                    skip_line_start_with="#",
                )
                Lookuptable.model_validate(self.lookup_tables[key])
        mix_energies = []
        max_energies = []
        pols = []
        poly1d_params = []
        for key in self.lookup_tables["Gap"].keys():
            if key is not None:
                pols.append(Pol[key])
                mix_energies.append(self.lookup_tables["Gap"][key]["Limit"]["Minimum"])
                max_energies.append(self.lookup_tables["Gap"][key]["Limit"]["Maximum"])
                poly1d_params.append(J09PhasePoly1dParameters[key])
        self.lookup_tables["Phase"] = make_phase_tables(
            pols=pols,
            min_energies=mix_energies,
            max_energies=max_energies,
            poly1d_params=poly1d_params,
        )
