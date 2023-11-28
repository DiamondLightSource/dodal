from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from dodal.devices.zocalo import NULL_RESULT, XrcResult, ZocaloInteractor, ZocaloResults


@pytest_asyncio.fixture
async def zocalo_device():
    zd = ZocaloResults("dev_artemis")
    await zd.connect()
    await zd.trigger()
    return zd


@pytest.mark.s03
@pytest.mark.asyncio
async def test_read_results_from_fake_zocalo():
    zc = ZocaloInteractor("dev_artemis")
