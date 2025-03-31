from dodal.devices.electron_analyser.abstract_region import EnergyMode


def to_kinetic_energy(
    value: float, excitation_energy: float, value_mode: EnergyMode
) -> float:
    return excitation_energy - value if value_mode == EnergyMode.BINDING else value


def to_binding_energy(
    value: float, excitation_energy: float, value_mode: EnergyMode
) -> float:
    return excitation_energy - value if value_mode == EnergyMode.KINETIC else value
