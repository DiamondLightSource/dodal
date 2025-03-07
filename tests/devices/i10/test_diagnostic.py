import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    get_mock_put,
)

from dodal.devices.i10.diagnostics import D3Position, D5APosition, Positioner


@pytest.fixture
async def mock_positioner(prefix: str = "BLXX-EA-007:") -> Positioner:
    async with init_devices(mock=True):
        mock_positioner = Positioner(prefix, positioner_enum=D3Position)
    assert mock_positioner.name == "mock_positioner"
    return mock_positioner


async def test_positioner_fail_wrong_value(mock_positioner: Positioner):
    with pytest.raises(ValueError):
        await mock_positioner.set(D5APosition.LA)


async def test_positioner_set_success(mock_positioner: Positioner):
    await mock_positioner.set(D3Position.GRID)
    get_mock_put(mock_positioner.stage_position).assert_awaited_once_with(
        D3Position.GRID, wait=True
    )
