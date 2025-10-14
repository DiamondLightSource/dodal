from dodal.devices.apple2_undulator import (
    Apple2,
    Apple2Controller,
    Apple2Val,
    EnergyMotorConvertor,
)
from dodal.log import LOGGER

ROW_PHASE_MOTOR_TOLERANCE = 0.004
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100
DEFAULT_JAW_PHASE_POLY_PARAMS = [1.0 / 7.5, -120.0 / 7.5]
ALPHA_OFFSET = 180
MAXIMUM_MOVE_TIME = 550  # There is no useful movements take longer than this.


class I17Apple2Controller(Apple2Controller[Apple2]):
    """
    I10Apple2Controller is a extension of Apple2Controller which provide linear
    arbitrary angle control.
    """

    def __init__(
        self,
        apple2: Apple2,
        energy_to_motor_converter: EnergyMotorConvertor,
        name: str = "",
    ) -> None:
        super().__init__(
            apple2=apple2,
            energy_to_motor_converter=energy_to_motor_converter,
            name=name,
        )

    async def _set_motors_from_energy(self, value: float) -> None:
        """
        Set the undulator motors for a given energy and polarisation.
        """

        pol = await self._check_and_get_pol_setpoint()
        gap, phase = self.energy_to_motor(energy=value, pol=pol)
        id_set_val = Apple2Val(
            top_outer=f"{phase:.6f}",
            top_inner="0.0",
            btm_inner=f"{phase:.6f}",
            btm_outer="0.0",
            gap=f"{gap:.6f}",
        )

        LOGGER.info(f"Setting polarisation to {pol}, with values: {id_set_val}")
        await self.apple2().set(id_motor_values=id_set_val)
