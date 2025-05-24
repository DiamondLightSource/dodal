import pytest

from dodal.devices.electron_analyser import to_binding_energy, to_kinetic_energy
from dodal.devices.electron_analyser.types import EnergyMode

ENERGY_MODE_PARAMS = [EnergyMode.KINETIC, EnergyMode.BINDING]


@pytest.mark.parametrize("energy_mode", ENERGY_MODE_PARAMS)
def test_to_kinetic_energy(energy_mode: EnergyMode) -> None:
    low_energy = 10
    excitation_energy = 5
    is_binding_energy = energy_mode == EnergyMode.BINDING

    ke = to_kinetic_energy(low_energy, energy_mode, excitation_energy)
    if is_binding_energy:
        assert ke == (excitation_energy - low_energy)
    else:
        assert ke == low_energy


@pytest.mark.parametrize("energy_mode", ENERGY_MODE_PARAMS)
def test_to_binding_energy(energy_mode: EnergyMode) -> None:
    low_energy = 10
    excitation_energy = 5
    is_binding_energy = energy_mode == EnergyMode.BINDING

    ke = to_binding_energy(low_energy, energy_mode, excitation_energy)
    if is_binding_energy:
        assert ke == low_energy
    else:
        assert ke == (excitation_energy - low_energy)
