import pytest

from dodal.devices.synchrotron import Synchrotron


@pytest.fixture
def synchrotron():
    synchrotron = Synchrotron("", name="synchrotron")
    return synchrotron


@pytest.mark.s03
async def test_synchrotron_connects(synchrotron: Synchrotron):
    await synchrotron.connect()
