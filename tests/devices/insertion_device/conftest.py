import pytest
from pytest import FixtureRequest

from dodal.devices.insertion_device import EnergyCoverage, LookupTable, Pol
from tests.devices.insertion_device.util import GenerateConfigLookupTable


@pytest.fixture(
    params=[
        # Single polarisation entry with multiple energy coverage entries e.g i10
        GenerateConfigLookupTable(
            polarisations=[Pol.LH],
            energy_coverage=[
                EnergyCoverage.generate(
                    min_energies=[100, 200],
                    max_energies=[200, 250],
                    poly1d_params=[[2.0, -1.0, 0.5], [1.0, 0.0]],
                )
            ],
        ),
        # Mutiple polarisation entries with single energy coverage entry e.g i09
        GenerateConfigLookupTable(
            polarisations=[Pol.LH, Pol.LV],
            energy_coverage=[
                EnergyCoverage.generate(
                    min_energies=[100], max_energies=[150], poly1d_params=[[1.0, 0.0]]
                ),
                EnergyCoverage.generate(
                    min_energies=[200], max_energies=[250], poly1d_params=[[0.5, 1.0]]
                ),
            ],
        ),
    ]
)
def generate_config_lut(request: FixtureRequest) -> GenerateConfigLookupTable:
    return request.param


@pytest.fixture
def lut(generate_config_lut: GenerateConfigLookupTable) -> LookupTable:
    return LookupTable.generate(
        pols=generate_config_lut.polarisations,
        energy_coverage=generate_config_lut.energy_coverage,
    )
