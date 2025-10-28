from daq_config_server.client import ConfigServer

from dodal.devices.apple2_undulator import Pol
from dodal.devices.util.lookup_tables_apple2 import (
    EnergyMotorLookup,
    Lookuptable,
    convert_csv_to_lookup,
    generate_lookup_table,
)
from dodal.log import LOGGER

ROW_PHASE_MOTOR_TOLERANCE = 0.004
ROW_PHASE_CIRCULAR = 15
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100
DEFAULT_JAW_PHASE_POLY_PARAMS = [1.0 / 7.5, -120.0 / 7.5]
ALPHA_OFFSET = 180
MAXIMUM_MOVE_TIME = 550  # There is no useful movements take longer than this.


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
            poly_deg=poly_deg,
        )

    def update_lookuptable(self):
        """
        Update lookup tables from files and validate their format.
        """
        LOGGER.info("Updating lookup dictionary from file.")
        for key, path in self.lookup_table_config.path.__dict__.items():
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
        min_energy = self.lookup_tables["Gap"]["LH"]["Limit"]["Minimum"]
        max_energy = self.lookup_tables["Gap"]["LH"]["Limit"]["Maximum"]
        self.lookup_tables["Phase"] = generate_lookup_table(
            pol=Pol.LH, min_energy=min_energy, max_energy=max_energy, poly1d_param=[0]
        )
        self.lookup_tables["Phase"].update(
            generate_lookup_table(
                pol=Pol.LH3,
                min_energy=min_energy,
                max_energy=max_energy,
                poly1d_param=[0],
            )
        )
        self.lookup_tables["Phase"].update(
            generate_lookup_table(
                pol=Pol.LV,
                min_energy=min_energy,
                max_energy=max_energy,
                poly1d_param=[MAXIMUM_ROW_PHASE_MOTOR_POSITION],
            )
        )

        self.lookup_tables["Phase"].update(
            generate_lookup_table(
                pol=Pol.PC,
                min_energy=min_energy,
                max_energy=max_energy,
                poly1d_param=[ROW_PHASE_CIRCULAR],
            )
        )
        self.lookup_tables["Phase"].update(
            generate_lookup_table(
                pol=Pol.NC,
                min_energy=min_energy,
                max_energy=max_energy,
                poly1d_param=[ROW_PHASE_CIRCULAR],
            )
        )
