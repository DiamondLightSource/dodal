from dodal.devices.electron_analyser import EnergyMode


def to_kinetic_energy(
    value: float, value_mode: EnergyMode, excitation_energy: float
) -> float:
    return excitation_energy - value if value_mode == EnergyMode.BINDING else value


def to_binding_energy(
    value: float, value_mode: EnergyMode, excitation_energy: float
) -> float:
    return excitation_energy - value if value_mode == EnergyMode.KINETIC else value
