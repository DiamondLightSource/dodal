import numpy as np
import pytest

from dodal.devices.insertion_device.apple2_undulator import Pol
from dodal.devices.insertion_device.lookup_table_models import (
    LookupTable,
    LookupTableConfig,
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
        assert lut.root[pol].limit.minimum == generate_config_lut.min_energies[i]
        assert lut.root[pol].limit.maximum == generate_config_lut.max_energies[i]
        assert generate_config_lut.min_energies[i] in lut.root[pol].energies.root

        poly = lut.root[pol].energies.root[generate_config_lut.min_energies[i]].poly
        test_energy = (
            generate_config_lut.min_energies[i] + generate_config_lut.max_energies[i]
        ) / 2.0
        assert poly(test_energy) == np.poly1d(generate_config_lut.polys[i])(test_energy)


def test_lookup_table_get_poly(
    lut: LookupTable, generate_config_lut: GenerateConfigLookupTable
) -> None:
    for i in range(len(generate_config_lut.polarisations)):
        expected_poly = np.poly1d(generate_config_lut.polys[i])
        poly = lut.get_poly(
            energy=generate_config_lut.min_energies[i],
            pol=generate_config_lut.polarisations[i],
        )
        assert poly == expected_poly


@pytest.fixture
def lut_config() -> LookupTableConfig:
    return LookupTableConfig(
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
    lut_config: LookupTableConfig,
) -> None:
    csv_content = (
        "Mode,MinEnergy,MaxEnergy,c1,c0\nHL,100,200,2.0,1.0\nVL,200,300,1.0,0.0\n"
    )
    lut = convert_csv_to_lookup(csv_content, lut_config)
    assert Pol.LH in lut.root
    assert Pol.LV in lut.root
    # Check polynomials evaluate as expected
    poly_lh = lut.root[Pol.LH].energies.root[100.0].poly
    assert isinstance(poly_lh, np.poly1d)
    assert poly_lh(150.0) == pytest.approx(np.poly1d([2.0, 1.0])(150.0))

    poly_lv = lut.root[Pol.LV].energies.root[200.0].poly
    assert isinstance(poly_lv, np.poly1d)
    assert poly_lv(250.0) == pytest.approx(np.poly1d([1.0, 0.0])(250.0))


def test_lookup_table_is_serialisable(lut: LookupTable) -> None:
    # There should be no errors when calling the below functions
    lut.model_dump()
    lut.model_dump_json()


async def test_bad_file_contents_causes_convert_csv_to_lookup_fails(
    lut_config: LookupTableConfig,
) -> None:
    with pytest.raises(RuntimeError):
        convert_csv_to_lookup("fnslkfndlsnf", lut_config)
