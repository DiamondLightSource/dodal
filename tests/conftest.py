import importlib
import logging
import os
import sys
from contextlib import contextmanager
from os import environ
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from daq_config_server.client import ConfigClient
from daq_config_server.testing import MockServerResponse, PathToMockDataDict
from ophyd_async.core import PathProvider

from dodal.common.beamlines import beamline_utils
from dodal.common.beamlines.beamline_utils import (
    clear_config_client,
    clear_path_provider,
)
from dodal.common.visit import (
    DirectoryServiceClient,
    LocalDirectoryServiceClient,
    StaticVisitPathProvider,
)
from dodal.device_manager import DeviceManager
from dodal.devices.detector import DetectorParams
from dodal.devices.detector.det_dim_constants import EIGER2_X_16M_SIZE
from dodal.log import LOGGER, GELFTCPHandler, set_up_all_logging_handlers
from dodal.utils import (
    DeviceInitializationController,
    collect_factories,
    make_all_devices,
)
from tests.devices.oav.test_data import TEST_DISPLAY_CONFIG, TEST_OAV_ZOOM_LEVELS
from tests.devices.test_daq_configuration import MOCK_DAQ_CONFIG_PATH
from tests.devices.test_data import TEST_LUT_TXT
from tests.test_data import I04_BEAMLINE_PARAMETERS, TEST_BEAMLINE_PARAMETERS_TXT

MOCK_ATTRIBUTES_TABLE: dict[str, dict[str, str]] = {
    "i03": {
        "BEAMLINE_PARAMETERS_PATH": TEST_BEAMLINE_PARAMETERS_TXT,
        "DAQ_CONFIGURATION_PATH": MOCK_DAQ_CONFIG_PATH,
        "ZOOM_PARAMS_FILE": TEST_OAV_ZOOM_LEVELS,
        "DISPLAY_CONFIG": TEST_DISPLAY_CONFIG,
    },
    "i04": {
        "BEAMLINE_PARAMETERS_PATH": I04_BEAMLINE_PARAMETERS,
        "DAQ_CONFIGURATION_PATH": MOCK_DAQ_CONFIG_PATH,
        "ZOOM_PARAMS_FILE": TEST_OAV_ZOOM_LEVELS,
        "DISPLAY_CONFIG": TEST_DISPLAY_CONFIG,
    },
    "i19_1": {
        "SHARED_CONFIG_PATH": MOCK_DAQ_CONFIG_PATH,
        "DAQ_CONFIGURATION_PATH": MOCK_DAQ_CONFIG_PATH,
        "ZOOM_PARAMS_FILE": TEST_OAV_ZOOM_LEVELS,
        "DISPLAY_CONFIG": TEST_DISPLAY_CONFIG,
    },
    "i19_2": {
        "SHARED_CONFIG_PATH": MOCK_DAQ_CONFIG_PATH,
    },
    "i19_optics": {
        "DAQ_CONFIGURATION_PATH": MOCK_DAQ_CONFIG_PATH,
    },
    "aithre": {
        "DISPLAY_CONFIG": TEST_DISPLAY_CONFIG,
        "ZOOM_PARAMS_FILE": TEST_OAV_ZOOM_LEVELS,
    },
    "i23": {
        "ZOOM_PARAMS_FILE": TEST_OAV_ZOOM_LEVELS,
        "DISPLAY_CONFIG": TEST_DISPLAY_CONFIG,
    },
    "i24": {
        "ZOOM_PARAMS_FILE": TEST_OAV_ZOOM_LEVELS,
        "DISPLAY_CONFIG": TEST_DISPLAY_CONFIG,
    },
}

BANNED_PATHS = [Path("/dls"), Path("/dls_sw")]
environ["DODAL_TEST_MODE"] = "true"


# Add run_engine, util fixtures, and mock_config_client to be used in tests
pytest_plugins = [
    "dodal.testing.fixtures.run_engine",
    "dodal.testing.fixtures.utils",
]


@pytest.fixture
def path_to_mock_data() -> PathToMockDataDict:
    return {}


@pytest.fixture
def mock_config_client(path_to_mock_data: PathToMockDataDict) -> ConfigClient:
    return ConfigClient(server_response=MockServerResponse(path_to_mock_data))


def is_path_banned(path: Path, banned_paths: list[Path]) -> bool:
    resolved = path.resolve()
    return resolved.is_absolute() and any(
        resolved.is_relative_to(banned) for banned in banned_paths
    )


@pytest.fixture(autouse=True)
def _allowed_bluesky_attr():
    os.environ["OPHYD_ASYNC_ALLOW_RESERVED_ATTRS"] = "YES"


@pytest.fixture(autouse=True)
def reset_path_provider():
    yield
    clear_path_provider()


@pytest.fixture(autouse=True)
def patch_open_to_prevent_dls_reads_in_tests():
    unpatched_open = open
    unpatched_path_open = Path.open

    def check_path(path: str | Path):
        requested_path = Path(path)
        if is_path_banned(requested_path, BANNED_PATHS):
            raise AssertionError(
                f"Attempt to open {requested_path} from inside a unit test"
            )

    def patched_open(file, *args, **kwargs):
        check_path(file)
        return unpatched_open(file, *args, **kwargs)

    def patched_path_open(self: Path, *args, **kwargs):
        check_path(self)
        return unpatched_path_open(self, *args, **kwargs)

    with (
        patch("builtins.open", side_effect=patched_open),
        patch.object(Path, "open", patched_path_open),
    ):
        yield


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


@contextmanager
def patch_all_config_clients(mock_config_client: ConfigClient):
    with patch.object(
        ConfigClient,
        "from_url",
        return_value=mock_config_client,
    ):
        yield


@pytest.fixture(scope="function")
def module_and_devices_for_beamline(
    mock_config_client: ConfigClient, request: pytest.FixtureRequest
):
    # Swap all ConfigClient get_file_contents instances with the mock one method.
    # Open local files for tests rather than from service.
    original_config_client = ConfigClient.get_file_contents
    ConfigClient.get_file_contents = mock_config_client.get_file_contents  # type: ignore

    beamline = request.param

    with patch_all_config_clients(mock_config_client):
        with patch.dict(os.environ, {"BEAMLINE": beamline}, clear=True):
            bl_mod = importlib.import_module("dodal.beamlines." + beamline)
            mock_beamline_module_filepaths(beamline, bl_mod)
            if isinstance(
                device_manager := getattr(bl_mod, "devices", None), DeviceManager
            ):
                result = device_manager.build_all(
                    include_skipped=True, mock=True
                ).connect()
                devices, exceptions = (
                    result.devices,
                    result.connection_errors | result.build_errors,
                )
            else:
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

            # Set back the ConfigClient instance with the original one.
            ConfigClient.get_file_contents = original_config_client


def mock_beamline_module_filepaths(bl_name: str, bl_module: ModuleType):
    if mock_attributes := MOCK_ATTRIBUTES_TABLE.get(bl_name):
        [bl_module.__setattr__(attr, value) for attr, value in mock_attributes.items()]


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


@pytest.fixture(autouse=True)
def reset_config_client():
    yield
    clear_config_client()
