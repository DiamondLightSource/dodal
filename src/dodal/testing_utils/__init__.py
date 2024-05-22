import asyncio
import time

import pytest
from bluesky.run_engine import RunEngine

from .device_fixtures import (
    ApSgAndLog,
    mock_aperturescatterguard,
    mock_aperturescatterguard_in_medium_pos,
    mock_aperturescatterguard_in_medium_pos_w_call_log,
    mock_aperturescatterguard_with_call_log,
    mock_backlight,
    mock_bart_robot,
    mock_dual_backlight,
    mock_eiger,
    mock_fast_grid_scan,
    mock_oav,
    mock_odin,
    mock_slits,
    mock_smargon,
    mock_synchrotron,
    mock_undulator_dcm,
    mock_vfm_mirror_voltages,
    test_aperture_positions,
)
from .utility_functions import (
    StatusException,
    assert_reading,
    create_new_detector_params,
    get_bad_status,
    mock_beamline_module_filepaths,
    patch_ophyd_async_motor,
    set_smargon_pos,
)

__all__ = [
    # Device fixtures
    "mock_aperturescatterguard",
    "mock_aperturescatterguard_in_medium_pos",
    "mock_aperturescatterguard_in_medium_pos_w_call_log",
    "mock_aperturescatterguard_with_call_log",
    "mock_backlight",
    "mock_bart_robot",
    "mock_dual_backlight",
    "mock_eiger",
    "mock_fast_grid_scan",
    "mock_oav",
    "mock_odin",
    "mock_smargon",
    "mock_synchrotron",
    "mock_slits",
    "mock_undulator_dcm",
    "mock_vfm_mirror_voltages",
    # Exceptions
    "StatusException",
    # Test data fixtures
    "test_aperture_positions",
    # Types
    "ApSgAndLog",
    # Utility functions
    "mock_beamline_module_filepaths",
    "patch_ophyd_async_motor",
    "set_smargon_pos",
    "get_bad_status",
    "create_new_detector_params",
    "assert_reading",
]


@pytest.fixture
async def RE():
    RE = RunEngine()
    # make sure the event loop is thoroughly up and running before we try to create
    # any ophyd_async devices which might need it
    timeout = time.monotonic() + 1
    while not RE.loop.is_running():
        await asyncio.sleep(0)
        if time.monotonic() > timeout:
            raise TimeoutError("This really shouldn't happen but just in case...")
    yield RE
