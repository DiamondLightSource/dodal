import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine

from dodal.devices.fast_grid_scan import (
    FastGridScan,
    GridScanParams,
    set_fast_grid_scan_params,
)


def wait_for_fgs_valid(fgs_motors: FastGridScan, timeout=0.5):
    SLEEP_PER_CHECK = 0.1
    times_to_check = int(timeout / SLEEP_PER_CHECK)
    for _ in range(times_to_check):
        scan_invalid = yield from bps.rd(fgs_motors.scan_invalid)
        pos_counter = yield from bps.rd(fgs_motors.position_counter)
        if not scan_invalid and pos_counter == 0:
            return
        yield from bps.sleep(SLEEP_PER_CHECK)
    raise Exception(f"Scan parameters invalid after {timeout} seconds")


@pytest.fixture()
def fast_grid_scan():
    fast_grid_scan = FastGridScan(name="fast_grid_scan", prefix="BL03S-MO-SGON-01:FGS:")
    yield fast_grid_scan


@pytest.mark.s03
async def test_when_program_data_set_and_staged_then_expected_images_correct(
    fast_grid_scan: FastGridScan, RE: RunEngine
):
    RE(
        set_fast_grid_scan_params(
            fast_grid_scan,
            GridScanParams(transmission_fraction=0.01, x_steps=2, y_steps=2),
        )
    )
    assert await fast_grid_scan.expected_images.get_value() == 2 * 2
    fast_grid_scan.stage()
    assert await fast_grid_scan.position_counter.get_value() == 0