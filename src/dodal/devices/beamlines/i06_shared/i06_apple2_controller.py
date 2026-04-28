from dodal.devices.insertion_device import (
    Apple2,
    Apple2Controller,
    Apple2PhasesVal,
    Apple2Val,
    Pol,
    UndulatorPhaseAxes,
)
from dodal.devices.insertion_device.energy_motor_lookup import EnergyMotorLookup


class I06Apple2Controller(Apple2Controller[Apple2[UndulatorPhaseAxes]]):
    """I06Apple2Controller extends Apple2Controller to provide specialized lookup-table
    control for the I06 Insertion Device.

    It manages bidirectional conversions between energy and motor positions (gap/phase)
    using dynamically updated polynomial lookup tables.

    Args:
        apple2 (Apple2): An Apple2 device with UndulatorPhaseAxes.
        gap_energy_motor_lut (EnergyMotorLookup): Handles Energy -> Gap lookup logic.
        phase_energy_motor_lut (EnergyMotorLookup): Handles Energy -> Phase lookup logic.
        gap_motor_energy_lut (EnergyMotorLookup): Handles Gap -> Energy inverse lookup logic.
        units (str, optional): The units for energy values. Defaults to "eV".
        name (str, optional): Name of the controller device.
    """

    def __init__(
        self,
        apple2: Apple2[UndulatorPhaseAxes],
        gap_energy_motor_lut: EnergyMotorLookup,
        phase_energy_motor_lut: EnergyMotorLookup,
        inverse_gap_energy_motor_lut: EnergyMotorLookup,
        units: str = "eV",
        name: str = "",
    ) -> None:
        super().__init__(
            apple2=apple2,
            gap_energy_motor_converter=gap_energy_motor_lut.find_value_in_lookup_table,
            phase_energy_motor_converter=phase_energy_motor_lut.find_value_in_lookup_table,
            inverse_gap_energy_motor_converter=inverse_gap_energy_motor_lut.find_value_in_lookup_table,
            units=units,
            name=name,
        )

    def _get_apple2_value(self, gap: float, phase: float, pol: Pol) -> Apple2Val:
        return Apple2Val(
            gap=gap,
            phase=Apple2PhasesVal(
                top_outer=phase,
                top_inner=0.0,
                btm_inner=phase,
                btm_outer=0.0,
            ),
        )
