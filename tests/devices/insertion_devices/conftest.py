from collections import namedtuple

import pytest
from pytest import FixtureRequest

from dodal.devices.insertion_device.apple2_undulator import Pol
from dodal.devices.insertion_device.lookup_table_models import (
    LookupTable,
    generate_lookup_table,
)

GenerateLookupTableConfig = namedtuple(
    "Config", ["polarisations", "min_energies", "max_energies", "polys"]
)


@pytest.fixture(
    params=[
        GenerateLookupTableConfig([Pol.LH], [100], [200], [[2.0, -1.0, 0.5]]),
        GenerateLookupTableConfig(
            [Pol.LH, Pol.LV], [100, 200], [150.0, 250.0], [[1.0, 0.0], [0.5, 1.0]]
        ),
    ]
)
def config(request: FixtureRequest) -> GenerateLookupTableConfig:
    return request.param


@pytest.fixture
def lut(config: GenerateLookupTableConfig) -> LookupTable:
    return generate_lookup_table(
        pols=config.polarisations,
        min_energies=config.min_energies,
        max_energies=config.max_energies,
        poly1d_params=config.polys,
    )
