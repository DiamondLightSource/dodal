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
from dodal.devices.electron_analyser.util import to_binding_energy, to_kinetic_energy
from dodal.devices.electron_analyser.vgscienta import VGScientaRegion, VGScientaSequence
from tests.devices.electron_analyser.helper_util import (
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


@pytest.mark.parametrize("field", ["low_energy", "centre_energy", "high_energy"])
@pytest.mark.parametrize("copy", [True, False])
@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
def test_each_energy_field_for_region_is_correct_when_switching_energy_modes(
    region: AbstractBaseRegion, field: str, copy: bool
) -> None:
    excitation_energy = 100
    conversion_func_map = {
        EnergyMode.KINETIC: to_binding_energy,
        EnergyMode.BINDING: to_kinetic_energy,
    }
    opposite_mode = {
        EnergyMode.KINETIC: EnergyMode.BINDING,
        EnergyMode.BINDING: EnergyMode.KINETIC,
    }
    original_energy = getattr(region, field)
    original_energy_mode = region.energy_mode
    conversion_func = conversion_func_map[region.energy_mode]
    converted_energy = conversion_func(
        original_energy, region.energy_mode, excitation_energy
    )

    e_mode_sequence = [
        original_energy_mode,
        opposite_mode[original_energy_mode],
        original_energy_mode,
    ]
    expected_e_values = [original_energy, converted_energy, original_energy]

    # Do full cycle of switching energy modes.
    # First check shouldn't see change as region is the same energy mode.
    # Second check cycles to the opposite energy mode, check it is correct via opposite
    # energy mode.
    # Third check cycles back so should be original value.
    for e_mode, e_expected in zip(e_mode_sequence, expected_e_values, strict=False):
        new_r = region.switch_energy_mode(e_mode, excitation_energy, copy)
        assert getattr(new_r, field) == e_expected
        assert new_r.energy_mode == e_mode
        if copy:
            assert new_r is not region
        else:
            assert new_r is region
