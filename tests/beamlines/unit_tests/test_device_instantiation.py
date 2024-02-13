import importlib
import os
from typing import Any
from unittest.mock import patch

import pytest

from dodal.beamlines import beamline_utils
from dodal.utils import BLUESKY_PROTOCOLS, make_all_devices

from ...conftest import mock_beamline_module_filepaths

ALL_BEAMLINES = {"i03", "i04", "i04_1", "i23", "i24", "p38", "p45"}


def follows_bluesky_protocols(obj: Any) -> bool:
    return any((isinstance(obj, protocol) for protocol in BLUESKY_PROTOCOLS))


def mock_bl(beamline):
    bl_mod = importlib.import_module("dodal.beamlines." + beamline)
    mock_beamline_module_filepaths(beamline, bl_mod)
    return bl_mod


@pytest.mark.parametrize("beamline", ALL_BEAMLINES)
def test_device_creation(RE, beamline):
    """
    Ensures that for every beamline all device factories are using valid args
    and creating types that conform to Bluesky protocols.
    """
    for bl in [beamline, "s" + beamline[1:]]:
        with patch.dict(os.environ, {"BEAMLINE": bl}, clear=True):
            bl_mod = mock_bl(beamline)
            devices = make_all_devices(bl_mod, fake_with_ophyd_sim=True)
            for device_name, device in devices.items():
                assert device_name in beamline_utils.ACTIVE_DEVICES
                assert follows_bluesky_protocols(device)
            assert len(beamline_utils.ACTIVE_DEVICES) == len(devices)
            beamline_utils.clear_devices()
            del bl_mod


@pytest.mark.parametrize("beamline", ALL_BEAMLINES)
def test_devices_are_identical(RE, beamline):
    """
    Ensures that for every beamline all device functions prevent duplicate instantiation.
    """
    for bl in [beamline, "s" + beamline[1:]]:
        with patch.dict(os.environ, {"BEAMLINE": beamline}, clear=True):
            bl_mod = mock_bl(beamline)
            devices_a = make_all_devices(bl_mod, fake_with_ophyd_sim=True)
            devices_b = make_all_devices(bl_mod, fake_with_ophyd_sim=True)
            for device_name in devices_a.keys():
                assert devices_a[device_name] is devices_b[device_name]
            beamline_utils.clear_devices()
            del bl_mod
