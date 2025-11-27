from collections import namedtuple

import numpy as np
import pytest
from pytest import FixtureRequest

from dodal.devices.apple2_undulator import Pol
from dodal.devices.util.lookup_tables_apple2 import (
    EnergyMotorLookup,
    LookupTableConfig,
    convert_csv_to_lookup,
    generate_lookup_table,
    read_file_and_skip,
)

Config = namedtuple(
    "Config", ["polarisations", "min_energies", "max_energies", "polys"]
)

TEST_PARAMS = [
    Config([Pol.LH], [100], [200], [[2.0, -1.0, 0.5]]),
    Config([Pol.LH, Pol.LV], [100, 200], [150.0, 250.0], [[1.0, 0.0], [0.5, 1.0]]),
]


@pytest.fixture(params=TEST_PARAMS)
def config(request: FixtureRequest) -> Config:
    return request.param


@pytest.fixture
def configured_energy_motor_lookup(config: Config) -> EnergyMotorLookup:
    return EnergyMotorLookup(
        lut=generate_lookup_table(
            pols=config.polarisations,
            min_energies=config.min_energies,
            max_energies=config.max_energies,
            poly1d_params=config.polys,
        )
    )


def test_configured_energy_motor_lookup_is_static(
    configured_energy_motor_lookup: EnergyMotorLookup,
) -> None:
    before_update_lut = configured_energy_motor_lookup.lut
    configured_energy_motor_lookup.update_lookup_table()
    after_update_lut = configured_energy_motor_lookup.lut
    assert before_update_lut == after_update_lut


def test_make_phase_tables_multiple_entries(
    config: Config,
    configured_energy_motor_lookup: EnergyMotorLookup,
) -> None:
    for i, pol in enumerate(config.polarisations):
        key = pol
        assert key in configured_energy_motor_lookup.lut.root
        entry = configured_energy_motor_lookup.lut.root[key]
        assert entry.limit.minimum == pytest.approx(config.min_energies[i])
        assert entry.limit.maximum == pytest.approx(config.max_energies[i])

        assert config.min_energies[i] in entry.energies.root
        poly = entry.energies.root[config.min_energies[i]].poly
        assert isinstance(poly, np.poly1d)

        test_energy = (config.min_energies[i] + config.max_energies[i]) / 2.0
        assert poly(test_energy) == pytest.approx(
            np.poly1d(config.polys[i])(test_energy)
        )


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


def test_lookup_table_is_serialisable(
    configured_energy_motor_lookup: EnergyMotorLookup,
) -> None:
    # There should be no errors when calling the below functions
    configured_energy_motor_lookup.lut.model_dump()
    configured_energy_motor_lookup.lut.model_dump_json()


async def test_bad_file_contents_causes_convert_csv_to_lookup_fails(
    lut_config: LookupTableConfig,
) -> None:
    with pytest.raises(RuntimeError):
        convert_csv_to_lookup("fnslkfndlsnf", lut_config)
