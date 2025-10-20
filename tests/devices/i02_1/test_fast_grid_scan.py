import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.i02_1.fast_grid_scan import (
    ZebraFastGridScanTwoD,
)


@pytest.fixture
async def fast_grid_scan():
    async with init_devices(mock=True):
        fast_grid_scan = ZebraFastGridScanTwoD(prefix="", motion_controller_prefix="")
    return fast_grid_scan


async def test_i02_1_gridscan_has_2d_behaviour(fast_grid_scan: ZebraFastGridScanTwoD):
    three_d_movables = ["z_step_size_mm", "z2_start_mm", "y2_start_mm", "z_steps"]
    for movable in three_d_movables:
        assert movable not in fast_grid_scan._movable_params.keys()
    set_mock_value(fast_grid_scan.x_steps, 5)
    set_mock_value(fast_grid_scan.y_steps, 4)
    assert await fast_grid_scan.expected_images.get_value() == 20
