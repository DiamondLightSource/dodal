from collections import namedtuple

import pytest
from pytest import FixtureRequest

from dodal.devices.insertion_device.apple2_undulator import Pol
from dodal.devices.insertion_device.lookup_table_models import (
    LookupTable,
    generate_lookup_table,
)

GenerateLookupTableConfig = namedtuple(
    "GenerateLookupTableConfig",
    ["polarisations", "min_energies", "max_energies", "polys"],
)


@pytest.fixture(
    params=[
        GenerateLookupTableConfig([Pol.LH], [100], [200], [[2.0, -1.0, 0.5]]),
        GenerateLookupTableConfig(
            [Pol.LH, Pol.LV], [100, 200], [150.0, 250.0], [[1.0, 0.0], [0.5, 1.0]]
        ),
    ]
)
def generate_lut_config(request: FixtureRequest) -> GenerateLookupTableConfig:
    return request.param


@pytest.fixture
def lut(generate_lut_config: GenerateLookupTableConfig) -> LookupTable:
    return generate_lookup_table(
        pols=generate_lut_config.polarisations,
        min_energies=generate_lut_config.min_energies,
        max_energies=generate_lut_config.max_energies,
        poly1d_params=generate_lut_config.polys,
    )
