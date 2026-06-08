from unittest.mock import patch

import pytest

from dodal.devices.beamlines import b07, b07_shared, i05_shared, i09
from dodal.devices.electron_analyser.base import (
    BaseRegion,
    EnergyMode,
    GenericRegion,
    GenericSequence,
    TBaseRegion,
    to_binding_energy,
    to_kinetic_energy,
)
from dodal.devices.electron_analyser.mbs import MbsRegion
from dodal.devices.electron_analyser.specs import SpecsRegion
from dodal.devices.electron_analyser.vgscienta import VGScientaRegion
from tests.devices.electron_analyser.helper_util import (
    load_b07_specs_test_seq,
    load_i05_mbs_test_xml_seq,
    load_i09_vgscienta_test_seq,
)


@pytest.mark.parametrize(
    "sequence, expected_region_names",
    [
        (load_b07_specs_test_seq(), ["New_Region", "New_Region1", "New_Region2"]),
        (load_i09_vgscienta_test_seq(), ["New_Region", "New_Region1", "New_Region2"]),
        (load_i05_mbs_test_xml_seq(), ["mbs_region1"]),
    ],
)
def test_sequence_get_expected_region_from_name(
    sequence: GenericSequence, expected_region_names: list[str]
) -> None:
    for name in expected_region_names:
        assert sequence.get_region_by_name(name) is not None
    assert sequence.get_region_by_name("region name should not be in sequence") is None


@pytest.mark.parametrize(
    "sequence, expected_enabled_region_names",
    [
        (load_b07_specs_test_seq(), ["New_Region1", "New_Region2"]),
        (load_i09_vgscienta_test_seq(), ["New_Region", "New_Region2"]),
        (load_i05_mbs_test_xml_seq(), ["mbs_region1"]),
    ],
)
def test_load_sequence_has_expected_enabled_region_names(
    sequence: GenericSequence, expected_enabled_region_names: list[str]
) -> None:
    assert sequence.get_enabled_region_names() == expected_enabled_region_names
    for i, region in enumerate(sequence.get_enabled_regions()):
        assert region.name == expected_enabled_region_names[i]


@pytest.mark.parametrize(
    "sequence, expected_region_class",
    [
        (load_b07_specs_test_seq(), SpecsRegion[b07.LensMode, b07_shared.PsuMode]),
        (load_i09_vgscienta_test_seq(), VGScientaRegion[i09.LensMode, i09.PassEnergy]),
        (
            load_i05_mbs_test_xml_seq(),
            MbsRegion[i05_shared.LensMode, i05_shared.PassEnergy],
        ),
    ],
)
def test_sequence_get_expected_region_type(
    sequence: GenericSequence,
    expected_region_class: type[TBaseRegion],
) -> None:
    regions = sequence.regions
    enabled_regions = sequence.get_enabled_regions()
    assert isinstance(regions, list) and all(
        isinstance(r, expected_region_class) for r in regions
    )
    assert isinstance(enabled_regions, list) and all(
        isinstance(r, expected_region_class) for r in enabled_regions
    )


@pytest.mark.parametrize(
    "sequence, expected_region_names",
    [
        (load_b07_specs_test_seq(), ["New_Region", "New_Region1", "New_Region2"]),
        (load_i09_vgscienta_test_seq(), ["New_Region", "New_Region1", "New_Region2"]),
        (load_i05_mbs_test_xml_seq(), ["mbs_region1"]),
    ],
)
def test_sequence_get_expected_region_names(
    sequence: GenericSequence, expected_region_names: list[str]
) -> None:
    assert sequence.get_region_names() == expected_region_names


ALL_REGION_TESTS_CASES = [
    *load_b07_specs_test_seq().regions,
    *load_i09_vgscienta_test_seq().regions,
    *load_i05_mbs_test_xml_seq().regions,
]


@pytest.mark.parametrize("region", ALL_REGION_TESTS_CASES)
def test_region_kinetic_and_binding_energy(region: GenericRegion) -> None:
    is_binding_energy = region.energy_mode == EnergyMode.BINDING
    is_kinetic_energy = region.energy_mode == EnergyMode.KINETIC
    assert region.is_binding_energy() == is_binding_energy
    assert region.is_binding_energy() != is_kinetic_energy
    assert region.is_kinetic_energy() == is_kinetic_energy
    assert region.is_kinetic_energy() != is_binding_energy


@pytest.mark.parametrize("field", ["low_energy", "centre_energy", "high_energy"])
@pytest.mark.parametrize("copy", [True, False])
@pytest.mark.parametrize("region", ALL_REGION_TESTS_CASES)
def test_each_energy_field_for_region_is_correct_when_switching_energy_modes(
    region: GenericRegion, field: str, copy: bool
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


@pytest.mark.parametrize("copy", [True, False])
@pytest.mark.parametrize("region", ALL_REGION_TESTS_CASES)
def test_region_prepare_for_epics(region: GenericRegion, copy: bool) -> None:
    # Patch switch_energy_mode so we can spy on if it was called while also returning
    # true function return value
    with patch.object(
        BaseRegion, "switch_energy_mode", wraps=region.switch_energy_mode
    ) as mock_switch_energy_mode:
        excitation_energy = 500
        original_energy_mode = region.energy_mode
        epics_region = region.prepare_for_epics(excitation_energy, copy)
        assert epics_region.energy_mode == original_energy_mode
        if copy:
            assert epics_region is not region
        else:
            assert epics_region is region
        mock_switch_energy_mode.assert_called_once_with(
            EnergyMode.KINETIC, excitation_energy, copy
        )
