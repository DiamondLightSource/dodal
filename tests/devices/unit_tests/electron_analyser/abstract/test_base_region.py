import pytest

from dodal.common.data_util import load_json_file_to_class
from dodal.devices import b07, i09
from dodal.devices.electron_analyser import EnergyMode
from dodal.devices.electron_analyser.abstract import (
    AbstractBaseRegion,
    AbstractBaseSequence,
    TAbstractBaseRegion,
)
from dodal.devices.electron_analyser.specs import (
    SpecsRegion,
    SpecsSequence,
)
from dodal.devices.electron_analyser.vgscienta import VGScientaRegion, VGScientaSequence
from tests.devices.unit_tests.electron_analyser.util import (
    TEST_SEQUENCE_REGION_NAMES,
    get_test_sequence,
)


@pytest.fixture(
    params=[
        SpecsSequence[b07.LensMode, b07.PsuMode],
        VGScientaSequence[i09.LensMode, i09.PsuMode, i09.PassEnergy],
    ]
)
def sequence(request: pytest.FixtureRequest) -> AbstractBaseSequence:
    return load_json_file_to_class(request.param, get_test_sequence(request.param))


@pytest.fixture
def expected_region_class(
    sequence: AbstractBaseSequence[AbstractBaseRegion],
) -> type[AbstractBaseRegion]:
    if isinstance(sequence, SpecsSequence):
        return SpecsRegion[b07.LensMode, b07.PsuMode]
    elif isinstance(sequence, VGScientaSequence):
        return VGScientaRegion[i09.LensMode, i09.PassEnergy]
    raise TypeError(f"Unknown sequence type {type(sequence)}")


@pytest.fixture
def expected_region_names() -> list[str]:
    return TEST_SEQUENCE_REGION_NAMES


def test_sequence_get_expected_region_from_name(
    sequence: AbstractBaseSequence[AbstractBaseRegion], expected_region_names: list[str]
) -> None:
    for name in expected_region_names:
        assert sequence.get_region_by_name(name) is not None
    assert sequence.get_region_by_name("region name should not be in sequence") is None


def test_sequence_get_expected_region_type(
    sequence: AbstractBaseSequence[AbstractBaseRegion],
    expected_region_class: type[TAbstractBaseRegion],
) -> None:
    regions = sequence.regions
    enabled_regions = sequence.get_enabled_regions()
    assert isinstance(regions, list) and all(
        isinstance(r, expected_region_class) for r in regions
    )
    assert isinstance(enabled_regions, list) and all(
        isinstance(r, expected_region_class) for r in enabled_regions
    )


def test_sequence_get_expected_region_names(
    sequence: AbstractBaseSequence[AbstractBaseRegion], expected_region_names: list[str]
) -> None:
    assert sequence.get_region_names() == expected_region_names


def test_region_kinetic_and_binding_energy(
    sequence: AbstractBaseSequence[AbstractBaseRegion],
) -> None:
    for r in sequence.regions:
        is_binding_energy = r.energy_mode == EnergyMode.BINDING
        is_kinetic_energy = r.energy_mode == EnergyMode.KINETIC
        assert r.is_binding_energy() == is_binding_energy
        assert r.is_binding_energy() != is_kinetic_energy
        assert r.is_kinetic_energy() == is_kinetic_energy
        assert r.is_kinetic_energy() != is_binding_energy
