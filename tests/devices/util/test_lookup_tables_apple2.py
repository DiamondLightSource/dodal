from unittest.mock import MagicMock

import numpy as np
import pytest
from daq_config_server.client import ConfigServer

from dodal.devices.apple2_undulator import Pol
from dodal.devices.util.lookup_tables_apple2 import (
    EnergyMotorLookup,
    LookupTableConfig,
    convert_csv_to_lookup,
    generate_lookup_table,
    make_phase_tables,
    read_file_and_skip,
)


def test_generate_lookup_table_structure_and_poly() -> None:
    min_e = 100.0
    max_e = 200.0
    coeffs = [2.0, -1.0, 0.5]
    lut = generate_lookup_table(
        pol=Pol.LH, min_energy=min_e, max_energy=max_e, poly1d_param=coeffs
    )

    key = Pol.LH
    assert key in lut.root

    entry = lut.root[key]
    assert entry.limit.minimum == pytest.approx(min_e)
    assert entry.limit.maximum == pytest.approx(max_e)

    assert min_e in entry.energies.root

    ec = entry.energies.root[min_e]
    assert ec.low == pytest.approx(min_e)
    assert ec.high == pytest.approx(max_e)

    assert isinstance(ec.poly, np.poly1d)
    expected = np.poly1d(coeffs)(150.0)
    assert ec.poly(150.0) == pytest.approx(expected)


def test_make_phase_tables_multiple_entries() -> None:
    pols = [Pol.LH, Pol.LV]
    min_energies = [100.0, 200.0]
    max_energies = [150.0, 250.0]
    poly_params = [[1.0, 0.0], [0.5, 1.0]]

    lut = make_phase_tables(
        pols=pols,
        min_energies=min_energies,
        max_energies=max_energies,
        poly1d_params=poly_params,
    )

    for i, pol in enumerate(pols):
        key = pol
        assert key in lut.root
        entry = lut.root[key]
        assert entry.limit.minimum == pytest.approx(min_energies[i])
        assert entry.limit.maximum == pytest.approx(max_energies[i])

        assert min_energies[i] in entry.energies.root
        poly = entry.energies.root[min_energies[i]].poly
        assert isinstance(poly, np.poly1d)

        test_energy = (min_energies[i] + max_energies[i]) / 2.0
        assert poly(test_energy) == pytest.approx(
            np.poly1d(poly_params[i])(test_energy)
        )


class DummyEnergyMotorLookup(EnergyMotorLookup):
    """Concrete test subclass that only populates the Gap table (Phase left empty)."""

    def _update_gap_lut(self) -> None:
        self.lookup_tables.gap = generate_lookup_table(
            pol=Pol.LH,
            min_energy=100.0,
            max_energy=200.0,
            poly1d_param=[2.0, -1.0, 0.5],
        )
        self.available_pol = list(self.lookup_tables.gap.root.keys())


@pytest.fixture
def lut_config() -> LookupTableConfig:
    return LookupTableConfig(
        mode="Mode",
        min_energy="MinEnergy",
        max_energy="MaxEnergy",
        poly_deg=["c1", "c0"],
        mode_name_convert={"hl": "lh", "vl": "lv"},
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


@pytest.fixture
def dummy_energy_motor_lookup(
    mock_config_client: ConfigServer,
    lut_config: LookupTableConfig,
) -> DummyEnergyMotorLookup:
    return DummyEnergyMotorLookup(
        config_client=mock_config_client,
        lut_config=lut_config,
        gap_path=None,
        phase_path=None,
    )


def test_energy_motor_lookup_with_phase_path_none(
    dummy_energy_motor_lookup: DummyEnergyMotorLookup,
) -> None:
    with pytest.raises(RuntimeError, match="Phase path is not provided"):
        dummy_energy_motor_lookup.update_lookuptables()


def test_energy_motor_lookup_with_gap_path_none(
    dummy_energy_motor_lookup: DummyEnergyMotorLookup,
) -> None:
    with pytest.raises(RuntimeError, match="Phase path is not provided"):
        dummy_energy_motor_lookup.update_lookuptables()


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
    dummy_energy_motor_lookup: DummyEnergyMotorLookup,
) -> None:
    csv_content = (
        "Mode,MinEnergy,MaxEnergy,c1,c0\nHL,100,200,2.0,1.0\nVL,200,300,1.0,0.0\n"
    )
    lut = convert_csv_to_lookup(csv_content, dummy_energy_motor_lookup.lut_config)
    assert Pol.LH in lut.root
    assert Pol.LV in lut.root
    # Check polynomials evaluate as expected
    poly_lh = lut.root[Pol.LH].energies.root[100.0].poly
    assert isinstance(poly_lh, np.poly1d)
    assert poly_lh(150.0) == pytest.approx(np.poly1d([2.0, 1.0])(150.0))

    poly_lv = lut.root[Pol.LV].energies.root[200.0].poly
    assert isinstance(poly_lv, np.poly1d)
    assert poly_lv(250.0) == pytest.approx(np.poly1d([1.0, 0.0])(250.0))

    # Assert phase dict is empty
    assert not dummy_energy_motor_lookup.lookup_tables.phase.root


def test_lookup_table_is_serialisable() -> None:
    lut = generate_lookup_table(
        pol=Pol.LH, min_energy=100, max_energy=200, poly1d_param=[2.0, -1.0, 0.5]
    )
    # There should be no errors when calling the below functions
    lut.model_dump()
    lut.model_dump_json()


async def test_bad_file_contents_causes_convert_csv_to_lookup_fails(
    dummy_energy_motor_lookup: DummyEnergyMotorLookup,
) -> None:
    with pytest.raises(RuntimeError):
        convert_csv_to_lookup(
            "fnslkfndlsnf",
            dummy_energy_motor_lookup.lut_config,
        )
