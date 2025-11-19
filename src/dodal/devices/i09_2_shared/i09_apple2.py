from pathlib import Path

from daq_config_server.client import ConfigServer

from dodal.devices.apple2_undulator import (
    MAXIMUM_MOVE_TIME,
    Apple2,
    Apple2Controller,
    Apple2PhasesVal,
    Apple2Val,
    Pol,
)
from dodal.devices.util.lookup_tables_apple2 import (
    EnergyMotorLookup,
    LookupTableConfig,
    generate_lookup_table_entry,
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
    mode_name_convert={"cr": "pc", "cl": "nc"},
)


class J09EnergyMotorLookup(EnergyMotorLookup):
    """
    Handles lookup tables for I10 Apple2 ID, converting energy and polarisation to gap
     and phase. Fetches and parses lookup tables from a config server, supports dynamic
     updates, and validates input.
    """

    def __init__(
        self,
        config_client: ConfigServer,
        lut_config: LookupTableConfig = J09DefaultLookupTableConfig,
        gap_path: Path | None = None,
        phase_path: Path | None = None,
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
            gap_path=gap_path,
            phase_path=phase_path,
        )

    def _update_phase_lut(self) -> None:
        if self.phase_path is None:
            for key in self.lookup_tables.gap.root.keys():
                if key is not None:
                    self.lookup_tables.phase.root[Pol(key.lower())] = (
                        generate_lookup_table_entry(
                            min_energy=self.lookup_tables.gap.root[
                                Pol(key.lower())
                            ].limit.minimum,
                            max_energy=self.lookup_tables.gap.root[
                                Pol(key.lower())
                            ].limit.maximum,
                            poly1d_param=(J09PhasePoly1dParameters[Pol(key.lower())]),
                        )
                    )
        else:
            super()._update_phase_lut()


class J09Apple2Controller(Apple2Controller[Apple2]):
    def __init__(
        self,
        apple2: Apple2,
        energy_motor_lut: J09EnergyMotorLookup,
        units: str = "keV",
        name: str = "",
    ) -> None:
        self.lookup_table_client = energy_motor_lut
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
                top_inner=f"{0.0:.6f}",
                btm_inner=f"{phase:.6f}",
                btm_outer=f"{0.0:.6f}",
            ),
        )

        LOGGER.info(f"Setting polarisation to {pol}, with values: {id_set_val}")
        await self.apple2().set(id_motor_values=id_set_val)

    async def _set_pol(
        self,
        value: Pol,
    ) -> None:
        # I09 require all palarisation change to go to LH first
        target_energy = await self.energy.get_value()
        if value is not Pol.LH:
            self._polarisation_setpoint_set(Pol.LH)
            max_lh_energy = float(
                self.lookup_table_client.lookup_tables.gap.root[Pol("lh")].limit.maximum
            )
            lh_setpoint = (
                max_lh_energy if target_energy > max_lh_energy else target_energy
            )
            await self.energy.set(lh_setpoint, timeout=MAXIMUM_MOVE_TIME)
        self._polarisation_setpoint_set(value)
        await self.energy.set(target_energy, timeout=MAXIMUM_MOVE_TIME)
