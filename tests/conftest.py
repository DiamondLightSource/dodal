import importlib
import logging
import os
import sys
from os import environ
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from ophyd_async.core import PathProvider

from dodal.common.beamlines import beamline_parameters, beamline_utils
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
from tests.devices.i10.test_data import LOOKUP_TABLE_PATH
from tests.devices.test_daq_configuration import MOCK_DAQ_CONFIG_PATH
from tests.devices.test_data import TEST_LUT_TXT
from tests.test_data import (
    I04_BEAMLINE_PARAMETERS,
    TEST_DISPLAY_CONFIG,
    TEST_OAV_ZOOM_LEVELS_XML,
)

MOCK_PATHS = [
    ("DAQ_CONFIGURATION_PATH", MOCK_DAQ_CONFIG_PATH),
    ("ZOOM_PARAMS_FILE", TEST_OAV_ZOOM_LEVELS_XML),
    ("DISPLAY_CONFIG", TEST_DISPLAY_CONFIG),
    ("LOOK_UPTABLE_DIR", LOOKUP_TABLE_PATH),
]
MOCK_ATTRIBUTES_TABLE = {
    "i03": MOCK_PATHS,
    "i10_optics": MOCK_PATHS,
    "i04": MOCK_PATHS,
    "i19_1": MOCK_PATHS,
    "i24": MOCK_PATHS,
    "aithre": MOCK_PATHS,
}

BANNED_PATHS = [Path("/dls"), Path("/dls_sw")]
environ["DODAL_TEST_MODE"] = "true"


# Add run_engine and util fixtures to be used in tests
pytest_plugins = ["dodal.testing.fixtures.run_engine", "dodal.testing.fixtures.utils"]


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
def module_and_devices_for_beamline(request: pytest.FixtureRequest):
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


def mock_beamline_module_filepaths(bl_name: str, bl_module: ModuleType):
    if mock_attributes := MOCK_ATTRIBUTES_TABLE.get(bl_name):
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
