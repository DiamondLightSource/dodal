import asyncio
import importlib
import logging
import os
import sys
import time
from collections.abc import Mapping
from os import environ, getenv
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from bluesky.run_engine import RunEngine
from ophyd.status import Status
from ophyd_async.core import (
    PathInfo,
    PathProvider,
)

from dodal.common.beamlines import beamline_parameters, beamline_utils
from dodal.common.visit import (
    DirectoryServiceClient,
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.log import LOGGER, GELFTCPHandler, set_up_all_logging_handlers
from dodal.utils import make_all_devices

MOCK_DAQ_CONFIG_PATH = "tests/devices/unit_tests/test_daq_configuration"
mock_paths = [
    ("DAQ_CONFIGURATION_PATH", MOCK_DAQ_CONFIG_PATH),
    ("ZOOM_PARAMS_FILE", "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"),
    ("DISPLAY_CONFIG", "tests/devices/unit_tests/test_display.configuration"),
    ("LOOK_UPTABLE_DIR", "tests/devices/i10/lookupTables/"),
]
mock_attributes_table = {
    "i03": mock_paths,
    "i10": mock_paths,
    "s03": mock_paths,
    "i04": mock_paths,
    "s04": mock_paths,
    "i24": mock_paths,
}

BANNED_PATHS = [Path("/dls"), Path("/dls_sw")]
environ["DODAL_TEST_MODE"] = "true"


@pytest.fixture(autouse=True)
def patch_open_to_prevent_dls_reads_in_tests():
    unpatched_open = open

    def patched_open(*args, **kwargs):
        requested_path = Path(args[0])
        if requested_path.is_absolute():
            for p in BANNED_PATHS:
                assert not requested_path.is_relative_to(
                    p
                ), f"Attempt to open {requested_path} from inside a unit test"
        return unpatched_open(*args, **kwargs)

    with patch("builtins.open", side_effect=patched_open):
        yield []


# Prevent pytest from catching exceptions when debugging in vscode so that break on
# exception works correctly (see: https://github.com/pytest-dev/pytest/issues/7409)
if os.getenv("PYTEST_RAISE", "0") == "1":

    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call: pytest.CallInfo[Any]):
        if call.excinfo is not None:
            raise call.excinfo.value
        else:
            raise RuntimeError(
                f"{call} has no exception data, an unknown error has occurred"
            )

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo: pytest.ExceptionInfo[Any]):
        raise excinfo.value


def mock_beamline_module_filepaths(bl_name, bl_module):
    if mock_attributes := mock_attributes_table.get(bl_name):
        [bl_module.__setattr__(attr[0], attr[1]) for attr in mock_attributes]
        beamline_parameters.BEAMLINE_PARAMETER_PATHS[bl_name] = (
            "tests/test_data/i04_beamlineParameters"
        )


@pytest.fixture(scope="function")
def module_and_devices_for_beamline(request):
    beamline = request.param
    with patch.dict(os.environ, {"BEAMLINE": beamline}, clear=True):
        bl_mod = importlib.import_module("dodal.beamlines." + beamline)
        importlib.reload(bl_mod)
        mock_beamline_module_filepaths(beamline, bl_mod)
        devices, exceptions = make_all_devices(
            bl_mod,
            include_skipped=True,
            fake_with_ophyd_sim=True,
        )
        yield (bl_mod, devices, exceptions)
        beamline_utils.clear_devices()
        del bl_mod


def pytest_runtest_setup(item):
    beamline_utils.clear_devices()
    if LOGGER.handlers == []:
        mock_graylog_handler = MagicMock(spec=GELFTCPHandler)
        mock_graylog_handler.return_value.level = logging.DEBUG

        with patch("dodal.log.GELFTCPHandler", mock_graylog_handler):
            set_up_all_logging_handlers(
                LOGGER, Path("./tmp/dev"), "dodal.log", True, 10000
            )


def pytest_runtest_teardown():
    if "dodal.beamlines.beamline_utils" in sys.modules:
        sys.modules["dodal.beamlines.beamline_utils"].clear_devices()


s03_epics_server_port = getenv("S03_EPICS_CA_SERVER_PORT")
s03_epics_repeater_port = getenv("S03_EPICS_CA_REPEATER_PORT")

if s03_epics_server_port is not None:
    environ["EPICS_CA_SERVER_PORT"] = s03_epics_server_port
    print(f"[EPICS_CA_SERVER_PORT] = {s03_epics_server_port}")
if s03_epics_repeater_port is not None:
    environ["EPICS_CA_REPEATER_PORT"] = s03_epics_repeater_port
    print(f"[EPICS_CA_REPEATER_PORT] = {s03_epics_repeater_port}")

PATH_INFO_FOR_TESTING: PathInfo = PathInfo(
    directory_path=Path("/does/not/exist"),
    filename="on_this_filesystem",
)


@pytest.fixture
def dummy_visit_client() -> DirectoryServiceClient:
    return LocalDirectoryServiceClient()


@pytest.fixture
async def static_path_provider(
    tmp_path: Path, dummy_visit_client: DirectoryServiceClient
) -> PathProvider:
    svpp = StaticVisitPathProvider(
        beamline="ixx", root=tmp_path, client=dummy_visit_client
    )
    await svpp.update()
    return svpp


@pytest.fixture
def run_engine_documents(RE: RunEngine) -> Mapping[str, list[dict]]:
    docs: dict[str, list[dict]] = {}

    def append_and_print(name, doc):
        if name not in docs:
            docs[name] = []
        docs[name] += [doc]

    RE.subscribe(append_and_print)
    return docs


def failed_status(failure: Exception) -> Status:
    status = Status()
    status.set_exception(failure)
    return status


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
