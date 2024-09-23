import pytest
from ophyd_async.core import DeviceCollector, PathProvider

from dodal.devices.i22.slits_collection import SlitsCollection


@pytest.fixture
def slits_collection(static_path_provider: PathProvider, RE) -> SlitsCollection:
    with DeviceCollector(mock=True):
        sc = SlitsCollection("six_slits", 6)
    return sc


async def test_config_data_present(slits_collection: SlitsCollection):
    assert len([slits_collection.slits]) == 6
    assert all(f"slits_{i}" in [slits_collection.slits] for i in range(1, 6))
    assert slits_collection.name == "six_slits"
