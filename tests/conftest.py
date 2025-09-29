import asyncio
import importlib
import os
import threading
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from random import random
from threading import Thread
from types import ModuleType
from unittest.mock import patch

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from conftest import mock_attributes_table
from dodal.common.beamlines import beamline_parameters, beamline_utils
from dodal.common.beamlines.commissioning_mode import set_commissioning_signal
from dodal.devices.baton import Baton
from dodal.devices.detector import DetectorParams
from dodal.devices.detector.det_dim_constants import EIGER2_X_16M_SIZE
from dodal.utils import (
    DeviceInitializationController,
    collect_factories,
    make_all_devices,
)
from tests.devices.test_data import TEST_LUT_TXT
from tests.test_data import I04_BEAMLINE_PARAMETERS


@pytest.fixture(scope="function")
def module_and_devices_for_beamline(request: pytest.FixtureRequest):
    beamline = request.param
    with patch.dict(os.environ, {"BEAMLINE": beamline}, clear=True):
        bl_mod = importlib.import_module("dodal.beamlines." + beamline)
        mock_beamline_module_filepaths(beamline, bl_mod)
        devices, exceptions = make_all_devices(
            bl_mod,
            include_skipped=True,
            fake_with_ophyd_sim=True,
        )
        yield (bl_mod, devices, exceptions)
        beamline_utils.clear_devices()
        for factory in collect_factories(bl_mod).values():
            if isinstance(factory, DeviceInitializationController):
                factory.cache_clear()
        del bl_mod


def mock_beamline_module_filepaths(bl_name: str, bl_module: ModuleType):
    if mock_attributes := mock_attributes_table.get(bl_name):
        [bl_module.__setattr__(attr[0], attr[1]) for attr in mock_attributes]
        beamline_parameters.BEAMLINE_PARAMETER_PATHS[bl_name] = I04_BEAMLINE_PARAMETERS


@pytest.fixture
def eiger_params(tmp_path: Path) -> DetectorParams:
    return DetectorParams(
        expected_energy_ev=100.0,
        exposure_time_s=1.0,
        directory=str(tmp_path),
        prefix="test",
        run_number=0,
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=1.0,
        num_images_per_trigger=1,
        num_triggers=2000,
        use_roi_mode=False,
        det_dist_to_beam_converter_path=TEST_LUT_TXT,
        detector_size_constants=EIGER2_X_16M_SIZE.det_type_string,  # type: ignore
    )


@pytest.fixture
async def baton_in_commissioning_mode() -> AsyncGenerator[Baton]:
    async with init_devices(mock=True):
        baton = Baton("BATON-01")
    set_commissioning_signal(baton.commissioning)
    set_mock_value(baton.commissioning, True)
    yield baton
    set_commissioning_signal(None)


@pytest.fixture
async def event_loop_fuzzing():
    """
    This fixture can be used to try and detect / reproduce intermittent test failures
    caused by race conditions and timing issues, which are often difficult to replicate
    due to caching etc. causing timing to be different on a development machine compared
    to when the test runs in CI.

    It works by attaching a fuzzer to the current event loop which randomly schedules
    a fixed delay into the event loop thread every few milliseconds. The idea is that
    over a number of iterations, there should be sufficient timing variation introduced
    that the failure can be reproduced.

    Examples:
        Example usage:
    >>> import pytest
    >>> # repeat the test a number of times
    >>> @pytest.mark.parametrize("i", range(0, 100))
    ... async def my_unreliable_test(i, event_loop_fuzzing):
    ...     # Do some stuff in here
    ...     ...
    """
    FUZZ_PROBABILITY = 0.05
    FUZZ_DELAY_S = 0.05
    FUZZ_PERIOD_S = 0.001
    stop_running = threading.Event()
    event_loop = asyncio.get_running_loop()

    def delay(finished_event: threading.Event):
        time.sleep(FUZZ_DELAY_S)
        finished_event.set()

    def fuzz():
        while not stop_running.is_set():
            if random() < FUZZ_PROBABILITY:
                delay_is_finished = threading.Event()
                event_loop.call_soon_threadsafe(delay, delay_is_finished)
                delay_is_finished.wait()

            time.sleep(FUZZ_PERIOD_S)

    fuzzer_thread = Thread(group=None, target=fuzz, name="Event loop fuzzer")
    fuzzer_thread.start()
    try:
        yield None
    finally:
        stop_running.set()
        fuzzer_thread.join()
