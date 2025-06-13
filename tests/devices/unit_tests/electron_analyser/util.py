import os
from typing import Any

from bluesky import plan_stubs as bps
from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor

from dodal.devices.electron_analyser import EnergyMode
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.specs import (
    SpecsAnalyserDriverIO,
    SpecsDetector,
    SpecsSequence,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaDetector,
    VGScientaSequence,
)

TEST_DATA_PATH = "tests/test_data/electron_analyser/"

TEST_VGSCIENTA_SEQUENCE = os.path.join(TEST_DATA_PATH, "vgscienta_sequence.seq")
TEST_SPECS_SEQUENCE = os.path.join(TEST_DATA_PATH, "specs_sequence.seq")

SEQUENCE_KEY = 0
SEQUENCE_TYPE_KEY = 1

TEST_SEQUENCES = {
    VGScientaDetector: [TEST_VGSCIENTA_SEQUENCE, VGScientaSequence],
    VGScientaAnalyserDriverIO: [TEST_VGSCIENTA_SEQUENCE, VGScientaSequence],
    SpecsDetector: [TEST_SPECS_SEQUENCE, SpecsSequence],
    SpecsAnalyserDriverIO: [TEST_SPECS_SEQUENCE, SpecsSequence],
}


def configure_driver_with_region(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    sim_energy_source: Motor,
):
    yield from bps.prepare(sim_driver, sim_energy_source)
    yield from bps.mv(sim_driver, region)


def get_test_sequence(key: type) -> str:
    return TEST_SEQUENCES[key][SEQUENCE_KEY]


def get_test_sequence_type(key: type) -> type[AbstractBaseSequence]:
    return TEST_SEQUENCES[key][SEQUENCE_TYPE_KEY]


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


async def assert_read_has_expected_value(
    device: StandardReadable, key: str, expected_value
) -> None:
    reading = await device.read()
    try:
        assert (
            reading[device.name + device._child_name_separator + key]["value"]
            == expected_value
        )
    except KeyError as e:
        raise KeyError(
            f'Cannot find key "{key}" in read method. Following keys '
            + f"are {reading.keys()}"
        ) from e


async def assert_read_configuration_has_expected_value(
    device: StandardReadable, key: str, expected_value
) -> None:
    read_config = await device.read_configuration()
    try:
        assert (
            read_config[device.name + device._child_name_separator + key]["value"]
            == expected_value
        )
    except KeyError as e:
        raise KeyError(
            f'Cannot find key "{key}" in read_configuration method. Following keys '
            + f"are {read_config.keys()}"
        ) from e
