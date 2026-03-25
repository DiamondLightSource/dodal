from dodal.devices.electron_analyser.base.base_enums import EnergyMode


def to_kinetic_energy(
    value: float, value_mode: EnergyMode, excitation_energy: float
) -> float:
    """Convert a value that is binding energy to kinetic energy.

    Args:
        value (float): The value to convert.
        value_mode (EnergyMode): Energy mode of the value. If it is already kinetic,
            return the same value. If it is binding, convert to kinetic.
        excitation_energy (float): Value to calculate the conversion.

    Returns:
        float: Caluclated kinetic energy value.
    """
    return value if value_mode == EnergyMode.KINETIC else excitation_energy - value


def to_binding_energy(
    value: float, value_mode: EnergyMode, excitation_energy: float
) -> float:
    """Convert a value that is kinetic energy to binding energy.

    Args:
        value (float): The value to convert.
        value_mode (EnergyMode): Energy mode of the value. If it is already binding,
            return the same value. If it is kinetic, convert to binding.
        excitation_energy (float): Value to calculate the conversion.

    Returns:
        float: Caluclated binding energy value.
    """
    return value if value_mode == EnergyMode.BINDING else excitation_energy - value
