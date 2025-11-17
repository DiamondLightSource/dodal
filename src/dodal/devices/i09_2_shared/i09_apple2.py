from daq_config_server.client import ConfigServer

from dodal.devices.apple2_undulator import (
    Apple2,
    Apple2Controller,
    Apple2PhasesVal,
    Apple2Val,
    Pol,
)
from dodal.devices.util.lookup_tables_apple2 import (
    BaseEnergyMotorLookup,
    LookupPath,
    LookupTableConfig,
    make_phase_tables,
)
from dodal.log import LOGGER

ROW_PHASE_MOTOR_TOLERANCE = 0.004
ROW_PHASE_CIRCULAR = 15
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100

J09PhasePoly1dParameters = {
    "lh": [0],
    "lv": [MAXIMUM_ROW_PHASE_MOTOR_POSITION],
    "pc": [ROW_PHASE_CIRCULAR],
    "nc": [-ROW_PHASE_CIRCULAR],
    "lh3": [0],
}


J09DefaultLookupTableConfig = LookupTableConfig(
    path=LookupPath.create(
        path="i09_apple2",
        gap_file="i09_apple2/j09_energy2gap_calibrations.csv",
        phase_file=None,
    ),
    mode="Mode",
    min_energy="MinEnergy",
    max_energy="MaxEnergy",
    poly_deg=[
        "9th-order",
        "8th-order",
        "7th-order",
        "6th-order",
        "5th-order",
        "4th-order",
        "3rd-order",
        "2nd-order",
        "1st-order",
        "0th-order",
    ],
)


class J09EnergyMotorLookup(BaseEnergyMotorLookup):
    """
    Handles lookup tables for I10 Apple2 ID, converting energy and polarisation to gap
     and phase. Fetches and parses lookup tables from a config server, supports dynamic
     updates, and validates input.
    """

    def __init__(
        self,
        config_client: ConfigServer,
        lut_config: LookupTableConfig = J09DefaultLookupTableConfig,
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
            config_client=config_client,
            lut_config=lut_config,
        )

    def update_lookuptable(self):
        """
        Update lookup tables from files and validate their format.
        """
        self.update_gap_lookuptable()
        mix_energies = []
        max_energies = []
        pols = []
        poly1d_params = []
        for key in self.lookup_tables[LookupTableKeys.GAP].keys():
            if key is not None:
                pols.append(Pol(key.lower()))
                mix_energies.append(
                    self.lookup_tables[LookupTableKeys.GAP][key][LookupTableKeys.LIMIT][
                        LookupTableKeys.MIN
                    ]
                )
                max_energies.append(
                    self.lookup_tables[LookupTableKeys.GAP][key][LookupTableKeys.LIMIT][
                        LookupTableKeys.MAX
                    ]
                )
                poly1d_params.append(J09PhasePoly1dParameters[key])
        self.lookup_tables[LookupTableKeys.PHASE] = make_phase_tables(
            pols=pols,
            min_energies=mix_energies,
            max_energies=max_energies,
            poly1d_params=poly1d_params,
        )
        Lookuptable.model_validate(self.lookup_tables[LookupTableKeys.PHASE])


class J09Apple2Controller(Apple2Controller[Apple2]):
    def __init__(
        self,
        apple2: Apple2,
        lookuptable_dir: str,
        config_client: ConfigServer,
        poly_deg: list[str] | None = None,
        units: str = "keV",
        name: str = "",
    ) -> None:
        self.lookup_table_client = J09EnergyMotorLookup(
            lookuptable_dir=lookuptable_dir,
            config_client=config_client,
            poly_deg=poly_deg,
        )
        super().__init__(
            apple2=apple2,
            energy_to_motor_converter=self.lookup_table_client.get_motor_from_energy,
            units=units,
            name=name,
        )

    async def _set_motors_from_energy(self, value: float) -> None:
        """
        Set the undulator motors for a given energy and polarisation.
        """

        pol = await self._check_and_get_pol_setpoint()
        gap, phase = self.energy_to_motor(energy=value, pol=pol)
        id_set_val = Apple2Val(
            gap=f"{gap:.6f}",
            phase=Apple2PhasesVal(
                top_outer=f"{phase:.6f}",
                top_inner="0.0",
                btm_inner=f"{phase:.6f}",
                btm_outer="0.0",
            ),
        )

        LOGGER.info(f"Setting polarisation to {pol}, with values: {id_set_val}")
        await self.apple2().set(id_motor_values=id_set_val)
