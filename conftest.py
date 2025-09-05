import asyncio
import logging
import sys
import time
from collections.abc import Mapping
from os import environ
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from bluesky.run_engine import RunEngine
from ophyd.status import Status
from ophyd_async.core import (
    PathInfo,
    PathProvider,
)
from tests.devices.i10.test_data import LOOKUP_TABLE_PATH
from tests.devices.test_daq_configuration import MOCK_DAQ_CONFIG_PATH
from tests.test_data import (
    TEST_DISPLAY_CONFIG,
    TEST_OAV_ZOOM_LEVELS_XML,
)

from dodal.common.beamlines import beamline_utils
from dodal.common.visit import (
    DirectoryServiceClient,
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.log import LOGGER, GELFTCPHandler, set_up_all_logging_handlers

mock_paths = [
    ("DAQ_CONFIGURATION_PATH", MOCK_DAQ_CONFIG_PATH),
    ("ZOOM_PARAMS_FILE", TEST_OAV_ZOOM_LEVELS_XML),
    ("DISPLAY_CONFIG", TEST_DISPLAY_CONFIG),
    ("LOOK_UPTABLE_DIR", LOOKUP_TABLE_PATH),
]
mock_attributes_table = {
    "i03": mock_paths,
    "i10": mock_paths,
    "i04": mock_paths,
    "s04": mock_paths,
    "i19_1": mock_paths,
    "i24": mock_paths,
    "aithre": mock_paths,
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
                assert not requested_path.is_relative_to(p), (
                    f"Attempt to open {requested_path} from inside a unit test"
                )
        return unpatched_open(*args, **kwargs)

    with patch("builtins.open", side_effect=patched_open):
        yield []


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


@pytest.fixture(scope="session", autouse=True)
async def _ensure_running_bluesky_event_loop():
    RE = RunEngine()
    # make sure the event loop is thoroughly up and running before we try to create
    # any ophyd_async devices which might need it
    timeout = time.monotonic() + 1
    while not RE.loop.is_running():
        await asyncio.sleep(0)
        if time.monotonic() > timeout:
            raise TimeoutError("This really shouldn't happen but just in case...")


@pytest.fixture()
async def RE():
    yield RunEngine()
