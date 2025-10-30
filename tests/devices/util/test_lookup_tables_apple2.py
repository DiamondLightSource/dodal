from unittest.mock import MagicMock

import numpy as np
import pytest
from daq_config_server.client import ConfigServer

from dodal.devices.apple2_undulator import Pol
from dodal.devices.util.lookup_tables_apple2 import (
    EnergyMotorLookup,
    convert_csv_to_lookup,
    generate_lookup_table,
    get_poly,
    make_phase_tables,
    read_file_and_skip,
)


@pytest.fixture
def mock_config_client() -> ConfigServer:
    mock_config_client = ConfigServer()

    mock_config_client.get_file_contents = MagicMock(spec=["get_file_contents"])

    def my_side_effect(file_path, reset_cached_result) -> str:
        assert reset_cached_result is True
        with open(file_path) as f:
            return f.read()

    mock_config_client.get_file_contents.side_effect = my_side_effect
    return mock_config_client


def test_generate_lookup_table_structure_and_poly():
    min_e = 100.0
    max_e = 200.0
    coeffs = [2.0, -1.0, 0.5]
    table = generate_lookup_table(
        pol=Pol.LH, min_energy=min_e, max_energy=max_e, poly1d_param=coeffs
    )

    key = Pol.LH.value
    assert key in table

    entry = table[key]
    assert entry["Limit"]["Minimum"] == pytest.approx(min_e)
    assert entry["Limit"]["Maximum"] == pytest.approx(max_e)

    energy_key = f"{min_e}"
    assert energy_key in entry["Energies"]

    ec = entry["Energies"][energy_key]
    assert ec["Low"] == pytest.approx(min_e)
    assert ec["High"] == pytest.approx(max_e)

    assert isinstance(ec["Poly"], np.poly1d)
    expected = np.poly1d(coeffs)(150.0)
    assert ec["Poly"](150.0) == pytest.approx(expected)


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
        assert key in table
        entry = table[key]
        assert entry["Limit"]["Minimum"] == pytest.approx(min_energies[i])
        assert entry["Limit"]["Maximum"] == pytest.approx(max_energies[i])

        energy_key = f"{min_energies[i]}"
        assert energy_key in entry["Energies"]
        poly = entry["Energies"][energy_key]["Poly"]
        assert isinstance(poly, np.poly1d)

        test_energy = (min_energies[i] + max_energies[i]) / 2.0
        assert poly(test_energy) == pytest.approx(
            np.poly1d(poly_params[i])(test_energy)
        )


class DummyLookup(EnergyMotorLookup):
    """Concrete test subclass that only populates the Gap table (Phase left empty)."""

    def update_lookuptable(self) -> None:
        # Populate only the Gap table and intentionally leave Phase empty
        self.lookup_tables["Gap"] = generate_lookup_table(
            pol=Pol.LH,
            min_energy=100.0,
            max_energy=200.0,
            poly1d_param=[2.0, -1.0, 0.5],
        )
        self.available_pol = list(self.lookup_tables["Gap"].keys())


def test_energy_motor_lookup_with_phase_path_none() -> None:
    lookup = DummyLookup(
        lookuptable_dir=".", config_client=MagicMock(), phase_file_name=None
    )
    assert lookup.lookup_table_config.path.Phase is None

    lookup.update_lookuptable()

    assert lookup.available_pol == [Pol.LH.value]

    poly = get_poly(150.0, Pol.LH, lookup.lookup_tables["Gap"])
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


def test_convert_csv_to_lookup_overwrite_name_convert_default() -> None:
    csv_content = (
        "Mode,MinEnergy,MaxEnergy,c1,c0\nHL,100,200,2.0,1.0\nVL,200,300,1.0,0.0\n"
    )

    lookuptable = convert_csv_to_lookup(
        file=csv_content,
        mode="Mode",
        min_energy="MinEnergy",
        max_energy="MaxEnergy",
        poly_deg=["c1", "c0"],
        mode_name_convert={"HL": "LH", "VL": "LV"},
    )

    assert "lh" in lookuptable
    assert "lv" in lookuptable
    print(lookuptable)
    # Check polynomials evaluate as expected
    poly_lh = lookuptable["lh"]["Energies"]["100"]["Poly"]
    assert isinstance(poly_lh, np.poly1d)
    assert poly_lh(150.0) == pytest.approx(np.poly1d([2.0, 1.0])(150.0))

    poly_lv = lookuptable["lv"]["Energies"]["200"]["Poly"]
    assert isinstance(poly_lv, np.poly1d)
    assert poly_lv(250.0) == pytest.approx(np.poly1d([1.0, 0.0])(250.0))
