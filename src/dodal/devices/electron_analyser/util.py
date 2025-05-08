from dodal.devices.electron_analyser.types import EnergyMode


def to_kinetic_energy(
    value: float, value_mode: EnergyMode, excitation_energy: float
) -> float:
    return value if value_mode == EnergyMode.KINETIC else excitation_energy - value


def to_binding_energy(
    value: float, value_mode: EnergyMode, excitation_energy: float
) -> float:
    return value if value_mode == EnergyMode.BINDING else excitation_energy - value
