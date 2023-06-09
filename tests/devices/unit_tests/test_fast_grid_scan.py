from dodal.devices.fast_grid_scan import FastGridScan, GridScanParams

test_params = {
    "detector_distance": 100.0,
    "dwell_time": 0.2,
    "exposure_time": 0.1,
    "omega_start": 0.0,
    "x_start": 0.0,
    "x_step_size": 0.1,
    "x_steps": 40,
    "y1_start": 0.0,
    "y2_start": 0.0,
    "y_step_size": 0.1,
    "y_steps": 20,
    "z1_start": 0.0,
    "z2_start": 0.0,
    "z_step_size": 0.1,
    "z_steps": 10,
}


def test_grid_scan_params():
    grid_scan_params = GridScanParams(**test_params)
    assert grid_scan_params.x_axis is not None
    assert grid_scan_params.y_axis is not None
    assert grid_scan_params.z_axis is not None
