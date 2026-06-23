import importlib
import json
import logging
import os
import sys
from collections.abc import Callable
from os import environ
from pathlib import Path
from types import ModuleType
from typing import Any, TypeVar
from unittest.mock import MagicMock, patch

import pytest
from daq_config_server import ConfigClient
from daq_config_server.models import ConfigModel
from ophyd_async.core import PathProvider
from pydantic import TypeAdapter

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

# ToDo - Make documentation so clearer for beamlines on how to fix tests by mocking the
# paths needed.
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


# Add run_engine and util fixtures to be used in tests
pytest_plugins = ["dodal.testing.fixtures.run_engine", "dodal.testing.fixtures.utils"]


@pytest.fixture(autouse=True)
def reset_path_provider():
    yield
    clear_path_provider()


T = TypeVar("T", str, dict, ConfigModel)


def fake_config_server_get_file_contents(
    file_path: str | Path,
    desired_return_type: type[T] = str,
    reset_cached_result: bool = True,
    force_parser: Callable[[str], Any] | None = None,
) -> T:
    """Fakes getting a file from the config server by reading it directly.

    Args:
        file_path (str | Path): Filepath of the file to read
        desired_return_type (type[T], optional): Type to convert the file to. Defaults to str.
        reset_cached_result (bool, optional): Whether or not to use the config server's cached result.
            Does nothing here as we don't cache. Defaults to True.
        force_parser (Callable[[str], Any] | None, optional): Use a certain converter function.
            Only needed for the interim where the converter exists but the config server has not
            been redeployed. Defaults to None.

    Raises:
        ValueError: Raised if an invalid type is requested

    Returns:
        T: The contents of the config file.
    """
    filepath = Path(file_path)
    if filepath.is_absolute():
        for p in BANNED_PATHS:
            assert not filepath.is_relative_to(p), (
                f"Attempt to open {filepath} from inside a unit test"
            )
    # Minimal logic required for unit tests
    with filepath.open("r") as f:
        contents = f.read()
    if force_parser:
        return TypeAdapter(desired_return_type).validate_python(force_parser(contents))
    if desired_return_type is str:
        return contents  # type: ignore
    if desired_return_type is dict:
        return json.loads(contents)
    if issubclass(desired_return_type, ConfigModel):
        return desired_return_type.model_validate(json.loads(contents))
    raise ValueError("Invalid return type requested")


@pytest.fixture
def mock_config_client() -> ConfigClient:
    # Don't actually talk to central service during unit tests, and reset caches between test
    mock_config_client = ConfigClient()
    mock_config_client.get_file_contents = MagicMock(spec=["get_file_contents"])

    mock_config_client.get_file_contents.side_effect = (
        fake_config_server_get_file_contents
    )
    return mock_config_client


def _is_banned(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path

    return resolved.is_absolute() and any(
        resolved.is_relative_to(banned) for banned in BANNED_PATHS
    )


@pytest.fixture(autouse=True)
def patch_open_to_prevent_dls_reads_in_tests():
    real_open = open

    def patched_open(*args, **kwargs):
        requested_path = Path(args[0])
        if _is_banned(requested_path):
            raise AssertionError(
                f"Attempt to open {requested_path} from inside a unit test"
            )
        return real_open(*args, **kwargs)

    with patch("builtins.open", side_effect=patched_open):
        yield []


@pytest.fixture(autouse=True)
def block_dls_access_in_config_client():

    def patch_get_file_contents(self, file_path, *args, **kwargs):
        path = Path(file_path)
        if _is_banned(path):
            raise AssertionError(f"Forbidden config access blocked in test: {path}")
        return ConfigClient.get_file_contents(self, file_path, *args, **kwargs)

    with patch.object(ConfigClient, "get_file_contents", new=patch_get_file_contents):
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


@pytest.fixture(scope="function")
def module_and_devices_for_beamline(
    mock_config_client: ConfigClient, request: pytest.FixtureRequest
):
    # Swap all ConfigClient instances with the mock one method.
    # Prevents dls paths used, open local files rather than from service.
    original_config_client = ConfigClient.get_file_contents
    ConfigClient.get_file_contents = mock_config_client.get_file_contents  # type: ignore

    beamline = request.param

    with patch.dict(os.environ, {"BEAMLINE": beamline}, clear=True):
        bl_mod = importlib.import_module("dodal.beamlines." + beamline)
        mock_beamline_module_filepaths(beamline, bl_mod)
        if isinstance(
            device_manager := getattr(bl_mod, "devices", None), DeviceManager
        ):
            result = device_manager.build_all(include_skipped=True, mock=True).connect()
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

        clear_config_client()
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
