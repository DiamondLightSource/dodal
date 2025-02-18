import importlib
import os
from unittest.mock import patch

import pytest

from conftest import mock_attributes_table
from dodal.beamlines import i03
from dodal.common.beamlines import beamline_parameters, beamline_utils
from dodal.utils import collect_factories, make_all_devices


@pytest.fixture(scope="function")
def module_and_devices_for_beamline(request):
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
        del bl_mod


def mock_beamline_module_filepaths(bl_name, bl_module):
    if mock_attributes := mock_attributes_table.get(bl_name):
        [bl_module.__setattr__(attr[0], attr[1]) for attr in mock_attributes]
        beamline_parameters.BEAMLINE_PARAMETER_PATHS[bl_name] = (
            "tests/test_data/i04_beamlineParameters"
        )


@pytest.fixture(scope="session")
def i03_device_factories():
    return [f for f in collect_factories(i03).values() if hasattr(f, "cache_clear")]


@pytest.fixture(scope="function", autouse=True)
def clear_device_factory_caches_after_every_test(i03_device_factories):
    yield None
    for f in i03_device_factories:
        f.cache_clear()  # type: ignore
