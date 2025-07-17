import pytest
from ophyd_async.core import StrictEnum, init_devices
from ophyd_async.testing import (
    get_mock_put,
)

from dodal.devices.positioner import Positioner1D, create_positioner


class Positions(StrictEnum):
    TEST_1 = "Test"
    TEST_2 = "Test_2"


class BadPositions(StrictEnum):
    BAD_POSITION = "BAD"


@pytest.fixture
async def mock_positioner() -> Positioner1D:
    async with init_devices(mock=True):
        mock_positioner = create_positioner(Positions, "BLXX-EA-007:")
    assert mock_positioner.name == "mock_positioner"
    return mock_positioner


async def test_positioner_fail_wrong_value(mock_positioner: Positioner1D[Positions]):
    with pytest.raises(ValueError):
        await mock_positioner.set(BadPositions.BAD_POSITION)  # type:ignore


async def test_positioner_set_success(mock_positioner: Positioner1D):
    await mock_positioner.set(Positions.TEST_1)
    get_mock_put(mock_positioner.stage_position).assert_awaited_once_with(
        Positions.TEST_1, wait=True
    )
