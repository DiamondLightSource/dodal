import numpy as np
import pytest
from pytest import FixtureRequest

from dodal.devices.insertion_device.apple2_undulator import Pol
from dodal.devices.insertion_device.lookup_table_models import LookupTable
from tests.devices.insertion_device.util import GenerateConfigLookupTable


@pytest.fixture(
    params=[
        GenerateConfigLookupTable(
            [Pol.LH], [100], [200], [np.poly1d([2.0, -1.0, 0.5])]
        ),
        GenerateConfigLookupTable(
            [Pol.LH, Pol.LV],
            [100, 200],
            [150.0, 250.0],
            [np.poly1d([1.0, 0.0]), np.poly1d([0.5, 1.0])],
        ),
    ]
)
def generate_config_lut(request: FixtureRequest) -> GenerateConfigLookupTable:
    return request.param


@pytest.fixture
def lut(generate_config_lut: GenerateConfigLookupTable) -> LookupTable:
    return LookupTable.generate(
        pols=generate_config_lut.polarisations,
        min_energies=generate_config_lut.min_energies,
        max_energies=generate_config_lut.max_energies,
        poly1d_params=generate_config_lut.polys,
    )
