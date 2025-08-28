import pytest
from ophyd_async.core import init_devices

from dodal.devices.i02_1.fast_grid_scan import (
    ZebraFastGridScanTwoD,
    ZebraGridScanParamsTwoD,
)


@pytest.fixture
async def fast_grid_scan():
    async with init_devices(mock=True):
        fast_grid_scan = ZebraFastGridScanTwoD(prefix="", smargon_prefix="")
    return fast_grid_scan


def test_i02_1_gridscan_only_has_2d_movables(fast_grid_scan: ZebraFastGridScanTwoD):
    assert "exposure_time_ms" in fast_grid_scan.movable_params.keys()
    three_d_movables = ["z_step_size_mm", "z2_start_mm", "y2_start_mm", "z_steps"]
    for movable in three_d_movables:
        assert movable not in fast_grid_scan.movable_params.keys()


def test_i02_1_gridscan_params_error_on_float_exposure_time():
    with pytest.raises(ValueError):
        ZebraGridScanParamsTwoD(transmission_fraction=1, exposure_time_ms=1.1)
