from dodal.devices.apple2_undulator import Apple2, Apple2Controller


# Inversion device on K07 does not exist yet - this class is a placeholder for when it does
class K07Apple2Controller(Apple2Controller):
    """K07 insertion device controller"""

    def __init__(
        self,
        apple2: Apple2,
        name: str = "",
    ) -> None:
        super().__init__(
            apple2=apple2,
            energy_to_motor_converter=lambda energy, pol: (0.0, 0.0),
            name=name,
        )

    async def _set_motors_from_energy(self, value: float) -> None:
        """
        Set the undulator motors for a given energy and polarisation.
        """
        pass
