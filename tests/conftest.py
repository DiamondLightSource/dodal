import importlib
import os
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest

from conftest import mock_attributes_table
from dodal.common.beamlines import beamline_parameters, beamline_utils
from dodal.devices.detector import DetectorParams
from dodal.devices.detector.det_dim_constants import EIGER2_X_16M_SIZE
from dodal.utils import (
    DeviceInitializationController,
    collect_factories,
    make_all_devices,
)


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
        beamline_parameters.BEAMLINE_PARAMETER_PATHS[bl_name] = (
            "tests/test_data/i04_beamlineParameters"
        )


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
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="tests/devices/unit_tests/test_lookup_table.txt",
        detector_size_constants=EIGER2_X_16M_SIZE.det_type_string,  # type: ignore
    )
