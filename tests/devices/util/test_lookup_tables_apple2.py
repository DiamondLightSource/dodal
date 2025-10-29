import numpy as np
import pytest

from dodal.devices.apple2_undulator import Pol
from dodal.devices.util.lookup_tables_apple2 import (
    generate_lookup_table,
    make_phase_tables,
)


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
