import numpy as np
import pytest

from dodal.devices.insertion_device import Pol
from dodal.devices.insertion_device.lookup_table_models import (
    EnergyCoverage,
    LookupTable,
    LookupTableColumnConfig,
    convert_csv_to_lookup,
    read_file_and_skip,
)
from tests.devices.insertion_device.util import GenerateConfigLookupTable


def test_lookup_table_generate(
    generate_config_lut: GenerateConfigLookupTable,
    lut: LookupTable,
) -> None:
    for i, pol in enumerate(generate_config_lut.polarisations):
        assert pol in lut.root
        expected_min_energy = generate_config_lut.energy_coverage[i].min_energy
        expected_max_energy = generate_config_lut.energy_coverage[i].max_energy
        assert lut.root[pol].min_energy == expected_min_energy
        assert lut.root[pol].max_energy == expected_max_energy

        poly = lut.root[pol].get_poly(expected_min_energy)
        test_energy = (expected_min_energy + expected_max_energy) / 2.0
        expected_poly = generate_config_lut.energy_coverage[i].get_poly(test_energy)
        assert poly(test_energy) == expected_poly(test_energy)


def test_lookup_table_get_poly(
    lut: LookupTable, generate_config_lut: GenerateConfigLookupTable
) -> None:
    for i in range(len(generate_config_lut.polarisations)):
        min_energy = generate_config_lut.energy_coverage[i].min_energy
        poly = lut.get_poly(
            energy=min_energy,
            pol=generate_config_lut.polarisations[i],
        )
        expected_poly = generate_config_lut.energy_coverage[i].get_poly(min_energy)
        assert poly == expected_poly


def test_lookup_table_is_serialisable(lut: LookupTable) -> None:
    # There should be no errors when calling the below functions
    lut.model_dump()
    lut.model_dump_json()


@pytest.fixture
def lut_config() -> LookupTableColumnConfig:
    return LookupTableColumnConfig(
        mode="Mode",
        min_energy="MinEnergy",
        max_energy="MaxEnergy",
        poly_deg=["c1", "c0"],
        mode_name_convert={"hl": "lh", "vl": "lv"},
    )


def test_read_file_and_skip_basic() -> None:
    content = (
        "# this is a comment line\n"
        "data_line_1,1,2,3\n"
        "# another comment\n"
        "data_line_2,4,5,6\n"
    )
    lines = list(read_file_and_skip(content))
    assert lines == ["data_line_1,1,2,3\n", "data_line_2,4,5,6\n"]


def test_convert_csv_to_lookup_overwrite_name_convert_default(
    lut_config: LookupTableColumnConfig,
) -> None:
    csv_content = (
        "Mode,MinEnergy,MaxEnergy,c1,c0\nHL,100,200,2.0,1.0\nVL,200,300,1.0,0.0\n"
    )
    lut = convert_csv_to_lookup(csv_content, lut_config)
    assert Pol.LH in lut.root
    assert Pol.LV in lut.root
    # Check polynomials evaluate as expected
    poly_lh = lut.root[Pol.LH].get_poly(100)
    assert poly_lh(150.0) == pytest.approx(np.poly1d([2.0, 1.0])(150.0))

    poly_lv = lut.root[Pol.LV].get_poly(200)
    assert poly_lv(250.0) == pytest.approx(np.poly1d([1.0, 0.0])(250.0))


async def test_bad_file_contents_causes_convert_csv_to_lookup_fails(
    lut_config: LookupTableColumnConfig,
) -> None:
    with pytest.raises(RuntimeError):
        convert_csv_to_lookup("fnslkfndlsnf", lut_config)


def test_energy_coverage_empty_entries_model_validate() -> None:
    ec = EnergyCoverage(energy_entries=())
    validated = EnergyCoverage.model_validate(ec)
    assert isinstance(validated, EnergyCoverage)
    assert validated.energy_entries == ()


def test_energy_coverage_get_energy_index() -> None:
    ec = EnergyCoverage.generate(
        min_energies=[300.0, 100.0, 200.0],
        max_energies=[400.0, 200.0, 300.0],
        poly1d_params=[[1.0], [2.0], [3.0]],
    )

    assert tuple(e.min_energy for e in ec.energy_entries) == (100.0, 200.0, 300.0)

    assert ec.get_energy_index(150.0) == 0
    assert ec.get_energy_index(250.0) == 1
    assert ec.get_energy_index(350.0) == 2


def test_energy_coverage_get_energy_index_gap_returns_none() -> None:
    ec = EnergyCoverage.generate(
        min_energies=[100.0, 160.0],
        max_energies=[150.0, 250.0],
        poly1d_params=[[1.0], [2.0]],
    )
    assert ec.get_energy_index(155.0) is None
