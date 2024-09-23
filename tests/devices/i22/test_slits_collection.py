import pytest
from ophyd_async.core import DeviceCollector, PathProvider

from dodal.devices.i22.slits_collection import SlitsCollection


@pytest.fixture
def slits_collection(static_path_provider: PathProvider, RE) -> SlitsCollection:
    with DeviceCollector(mock=True):
        six_slits = SlitsCollection("six_slits", 6)
    return six_slits


async def test_config_data_present(slits_collection: SlitsCollection):
    assert len(slits_collection.slits.keys()) == 6
    names_list: list[str] = [slit.name for _, slit in slits_collection.slits.items()]
    assert all(f"six_slits-slits-{i}" in names_list for i in range(1, 5))
    assert slits_collection.name == "six_slits"
