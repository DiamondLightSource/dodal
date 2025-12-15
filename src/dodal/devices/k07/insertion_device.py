from dodal.devices.apple2_undulator import (
    Apple2,
    Apple2Controller,
    Apple2PhasesVal,
    Apple2Val,
    Pol,
    UndulatorPhaseAxes,
)
from dodal.devices.util.lookup_tables_apple2 import EnergyMotorLookup

K07_GAP_POLY_DEG_COLUMNS = [
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
]

K07_PHASE_POLY_DEG_COLUMNS = ["0th-order"]


# Inversion device on K07 does not exist yet - this class is a placeholder for when it does
class K07Apple2Controller(Apple2Controller[Apple2[UndulatorPhaseAxes]]):
    """K07 insertion device controller"""

    def __init__(
        self,
        apple2: Apple2[UndulatorPhaseAxes],
        gap_energy_motor_lut: EnergyMotorLookup,
        phase_energy_motor_lut: EnergyMotorLookup,
        units: str = "keV",
        name: str = "",
    ) -> None:
        """
        Parameters:
        -----------
        apple2 : Apple2
            An Apple2 device.
        gap_energy_motor_lut: EnergyMotorLookup
            The class that handles the gap look up table logic for the insertion device.
        phase_energy_motor_lut: EnergyMotorLookup
            The class that handles the phase look up table logic for the insertion device.
        units:
            the units of this device. Defaults to eV.
        name : str, optional
            New device name.
        """
        self.gap_energy_motor_lut = gap_energy_motor_lut
        self.phase_energy_motor_lut = phase_energy_motor_lut
        super().__init__(
            apple2=apple2,
            gap_energy_motor_converter=gap_energy_motor_lut.find_value_in_lookup_table,
            phase_energy_motor_converter=phase_energy_motor_lut.find_value_in_lookup_table,
            units=units,
            name=name,
        )

    def _get_apple2_value(self, gap: float, phase: float, pol: Pol) -> Apple2Val:
        """
        This method should be implemented by the beamline specific ID class as the
        motor positions will be different for each beamline depending on the
        undulator design.
        """
        return Apple2Val(
            gap=f"{gap:.6f}",
            phase=Apple2PhasesVal(
                top_outer=f"{phase:.6f}",
                top_inner=f"{0.0:.6f}",
                btm_inner=f"{phase:.6f}",
                btm_outer=f"{0.0:.6f}",
            ),
        )
