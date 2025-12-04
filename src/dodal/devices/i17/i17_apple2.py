from dodal.devices.insertion_device.apple2_undulator import (
    Apple2,
    Apple2Controller,
    Apple2PhasesVal,
    Apple2Val,
    Pol,
    UndulatorPhaseAxes,
)
from dodal.devices.insertion_device.energy_motor_lookup import EnergyMotorLookup

ROW_PHASE_MOTOR_TOLERANCE = 0.004
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100
DEFAULT_JAW_PHASE_POLY_PARAMS = [1.0 / 7.5, -120.0 / 7.5]
ALPHA_OFFSET = 180
MAXIMUM_MOVE_TIME = 550  # There is no useful movements take longer than this.


class I17Apple2Controller(Apple2Controller[Apple2[UndulatorPhaseAxes]]):
    """
    I10Apple2Controller is a extension of Apple2Controller which provide linear
    arbitrary angle control.
    """

    def __init__(
        self,
        apple2: Apple2[UndulatorPhaseAxes],
        gap_energy_motor_lut: EnergyMotorLookup,
        phase_energy_motor_lut: EnergyMotorLookup,
        units: str = "eV",
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
        return Apple2Val(
            gap=f"{gap:.6f}",
            phase=Apple2PhasesVal(
                top_outer=f"{phase:.6f}",
                top_inner=f"{0.0:.6f}",
                btm_inner=f"{phase:.6f}",
                btm_outer=f"{0.0:.6f}",
            ),
        )
