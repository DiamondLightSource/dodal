from typing import Any

from ophyd_async.core import StandardReadable

from dodal.devices.electron_analyser import EnergyMode
from dodal.devices.electron_analyser.abstract_region import AbstractBaseRegion

TEST_VGSCIENTA_SEQUENCE = "vgscienta_sequence.seq"
TEST_SPECS_SEQUENCE = "specs_sequence.seq"
TEST_SEQUENCE_REGION_NAMES = ["New_Region", "New_Region1"]


def assert_region_kinetic_and_binding_energy(r: AbstractBaseRegion) -> None:
    is_binding_energy = r.energy_mode == EnergyMode.BINDING
    is_kinetic_energy = r.energy_mode == EnergyMode.KINETIC
    assert r.is_binding_energy() == is_binding_energy
    assert r.is_binding_energy() != is_kinetic_energy
    assert r.is_kinetic_energy() == is_kinetic_energy
    assert r.is_kinetic_energy() != is_binding_energy


def assert_region_has_expected_values(
    r: AbstractBaseRegion, expected_region_values: dict[str, Any]
) -> None:
    for key in r.__dict__:
        if key in expected_region_values:
            assert r.__dict__[key] == expected_region_values[key]
        else:
            raise KeyError('key "' + key + '" is not in the expected values.')


async def assert_reading_has_expected_value(
    device: StandardReadable, key: str, expected_value
) -> None:
    reading = await device.read()
    assert (
        reading[device.name + device._child_name_separator + key]["value"]
        == expected_value
    )
