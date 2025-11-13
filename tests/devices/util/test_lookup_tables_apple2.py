from unittest.mock import MagicMock

import numpy as np
import pytest

from dodal.devices.apple2_undulator import Pol
from dodal.devices.util.lookup_tables_apple2 import (
    BaseEnergyMotorLookup,
    LookupTableColumnConfig,
    convert_csv_to_lookup,
    create_lookup_path,
    generate_lookup_table,
    get_poly,
    make_phase_tables,
    read_file_and_skip,
)


def test_generate_lookup_table_structure_and_poly():
    min_e = 100.0
    max_e = 200.0
    coeffs = [2.0, -1.0, 0.5]
    table = generate_lookup_table(
        pol=Pol.LH, min_energy=min_e, max_energy=max_e, poly1d_param=coeffs
    )

    key = Pol.LH.value
    assert key in table.root

    entry = table.root[key]
    assert entry.limit.minimum == pytest.approx(min_e)
    assert entry.limit.maximum == pytest.approx(max_e)

    energy_key = f"{min_e}"
    assert energy_key in entry.energies.root

    ec = entry.energies.root[energy_key]
    assert ec.low == pytest.approx(min_e)
    assert ec.high == pytest.approx(max_e)

    assert isinstance(ec.poly, np.poly1d)
    expected = np.poly1d(coeffs)(150.0)
    assert ec.poly(150.0) == pytest.approx(expected)


def test_make_phase_tables_multiple_entries():
    pols = [Pol.LH, Pol.LV]
    min_energies = [100.0, 200.0]
    max_energies = [150.0, 250.0]
    poly_params = [[1.0, 0.0], [0.5, 1.0]]

    table = make_phase_tables(
        pols=pols,
        min_energies=min_energies,
        max_energies=max_energies,
        poly1d_params=poly_params,
    )

    for i, pol in enumerate(pols):
        key = pol.value
        assert key in table.root
        entry = table.root[key]
        assert entry.limit.minimum == pytest.approx(min_energies[i])
        assert entry.limit.maximum == pytest.approx(max_energies[i])

        energy_key = f"{min_energies[i]}"
        assert energy_key in entry.energies.root
        poly = entry.energies.root[energy_key].poly
        assert isinstance(poly, np.poly1d)

        test_energy = (min_energies[i] + max_energies[i]) / 2.0
        assert poly(test_energy) == pytest.approx(
            np.poly1d(poly_params[i])(test_energy)
        )


class DummyLookup(BaseEnergyMotorLookup):
    """Concrete test subclass that only populates the Gap table (Phase left empty)."""

    def update_lookuptable(self) -> None:
        # Populate only the Gap table and intentionally leave Phase empty
        self.lookup_tables.gap = generate_lookup_table(
            pol=Pol.LH,
            min_energy=100.0,
            max_energy=200.0,
            poly1d_param=[2.0, -1.0, 0.5],
        )
        self.available_pol = list(self.lookup_tables.gap.root.keys())


@pytest.fixture
def lut_column_config() -> LookupTableColumnConfig:
    return LookupTableColumnConfig(
        path=create_lookup_path(
            ".",
        ),
        mode="Mode",
        min_energy="MinEnergy",
        max_energy="MaxEnergy",
        poly_deg=["c1", "c0"],
        mode_name_convert={"hl": "lh", "vl": "lv"},
    )


@pytest.fixture
def dummy_lookup(lut_column_config: LookupTableColumnConfig) -> DummyLookup:
    return DummyLookup(
        config_client=MagicMock(),
        lut_column_config=lut_column_config,
    )


def test_energy_motor_lookup_with_phase_path_none(dummy_lookup: DummyLookup) -> None:
    # assert dummy_lookup.lut_column_config.path.phase is None

    dummy_lookup.update_lookuptable()

    assert dummy_lookup.available_pol == [Pol.LH.value]

    poly = get_poly(150.0, Pol.LH, dummy_lookup.lookup_tables.gap)
    assert isinstance(poly, np.poly1d)
    assert poly(150.0) == pytest.approx(np.poly1d([2.0, -1.0, 0.5])(150.0))


def test_read_file_and_skip_basic():
    content = (
        "# this is a comment line\n"
        "data_line_1,1,2,3\n"
        "# another comment\n"
        "data_line_2,4,5,6\n"
    )

    lines = list(read_file_and_skip(content))
    assert lines == ["data_line_1,1,2,3\n", "data_line_2,4,5,6\n"]


def test_convert_csv_to_lookup_overwrite_name_convert_default(
    lut_column_config: LookupTableColumnConfig,
) -> None:
    csv_content = (
        "Mode,MinEnergy,MaxEnergy,c1,c0\nHL,100,200,2.0,1.0\nVL,200,300,1.0,0.0\n"
    )

    lookuptable = convert_csv_to_lookup(csv_content, lut_column_config)

    assert "lh" in lookuptable.root
    assert "lv" in lookuptable.root
    # Check polynomials evaluate as expected
    poly_lh = lookuptable.root["lh"].energies.root["100.0"].poly
    assert isinstance(poly_lh, np.poly1d)
    assert poly_lh(150.0) == pytest.approx(np.poly1d([2.0, 1.0])(150.0))

    poly_lv = lookuptable.root["lv"].energies.root["200.0"].poly
    assert isinstance(poly_lv, np.poly1d)
    assert poly_lv(250.0) == pytest.approx(np.poly1d([1.0, 0.0])(250.0))
