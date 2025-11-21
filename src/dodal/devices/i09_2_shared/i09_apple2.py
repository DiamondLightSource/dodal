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
)
from dodal.log import LOGGER

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


class J09Apple2Controller(Apple2Controller[Apple2]):
    def __init__(
        self,
        apple2: Apple2,
        energy_motor_lut: EnergyMotorLookup,
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
        # I09 require all palarisation change to go via LH.
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
