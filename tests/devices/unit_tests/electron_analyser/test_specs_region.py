import pytest
from tests.devices.unit_tests.electron_analyser.test_utils import (
    check_region_model_list_to_expected_values,
)

from dodal.devices.electron_analyser.base_region import EnergyMode
from dodal.devices.electron_analyser.specs_region import SpecsSequence


@pytest.fixture
def sequence_file() -> str:
    return "vgscienta_sequence.seq"


@pytest.fixture
def sequence_class() -> type[SpecsSequence]:
    return SpecsSequence


def get_expected_region_values():
    return [
        {
            "name": "region",
            "acquisitionMode": "Fixed Transmission",
            "psuMode": "3.5kV",
            "lensMode": "SmallArea",
            "lowEnergy": 800.0,
            "highEnergy": 850.0,
            "energyStep": 0.1,
            "passEnergy": 5.0,
            "iterations": 1,
            "stepTime": 1.0,
            "enabled": False,
            "energyMode": EnergyMode.KINETIC,
            "values": 1,
            "slices": 100,
            "centreEnergy": 0.0,
            "estimatedTimeInMs": 0,
        },
        {
            "name": "region2",
            "acquisitionMode": "Snapshot",
            "psuMode": "1.5kV",
            "lensMode": "LargeArea",
            "lowEnergy": 599.866,
            "highEnergy": 600.134,
            "energyStep": 0.2680000000000291,
            "passEnergy": 2.0,
            "iterations": 5,
            "stepTime": 2.0,
            "enabled": True,
            "energyMode": EnergyMode.BINDING,
            "values": 1,
            "slices": 110,
            "centreEnergy": 0.0,
            "estimatedTimeInMs": 13718,
        },
    ]


def test_specs_file_loads_into_class(sequence):
    assert sequence.get_region_names() == ["region", "region2"]
    assert sequence.get_enabled_region_names() == ["region2"]

    check_region_model_list_to_expected_values(
        sequence.regions, get_expected_region_values()
    )
