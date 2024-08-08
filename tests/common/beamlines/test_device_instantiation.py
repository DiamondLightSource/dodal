import importlib.util
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from dodal.beamlines import all_beamline_modules
from dodal.common.beamlines import beamline_utils
from dodal.utils import (
    BLUESKY_PROTOCOLS,
    get_beamline_based_on_environment_variable,
    make_all_devices,
)


def get_module_name_by_beamline_name(name: str) -> Iterable[str]:
    """
    Get the names of specific importable modules that match the beamline name.

    Args:
        name (str): The beamline name to filter modules.

    Returns:
        Iterable[str]: An iterable of matching beamline module names.
    """

    # This is done by inspecting file names rather than modules to avoid
    # premature importing
    spec = importlib.util.find_spec("dodal.beamlines")
    if spec is not None:
        assert spec.submodule_search_locations
        search_paths = [Path(path) for path in spec.submodule_search_locations]
        # todo the error is here in the search paths
        # possibly has to do with the execution location, in dodal.beamlines this worked, not here

        for path in search_paths:
            for subpath in path.glob("**/*"):
                if (
                    subpath.name.endswith(".py")
                    and subpath.name != "__init__.py"
                    and ("__pycache__" not in str(subpath))
                ):
                    module_name = subpath.with_suffix("").name
                    if name in module_name:
                        yield module_name
    else:
        raise KeyError(f"Unable to find {__name__} module")


def follows_bluesky_protocols(obj: Any) -> bool:
    return any(isinstance(obj, protocol) for protocol in BLUESKY_PROTOCOLS)


@pytest.mark.parametrize(
    "module_and_devices_for_beamline",
    set(all_beamline_modules()),
    indirect=True,
)
def test_device_creation(RE, module_and_devices_for_beamline):
    """
    Ensures that for every beamline all device factories are using valid args
    and creating types that conform to Bluesky protocols.
    """
    _, devices = module_and_devices_for_beamline
    for device_name, device in devices.items():
        assert device_name in beamline_utils.ACTIVE_DEVICES, (
            f"No device named {device_name} was created for {module}, "
            f"devices are {beamline_utils.ACTIVE_DEVICES.keys()}"
        )
        assert follows_bluesky_protocols(device)
    assert len(beamline_utils.ACTIVE_DEVICES) == len(devices)


@pytest.mark.parametrize(
    "mappings",
    set({"i22": "p38"}),
    indirect=True,
)
def test_lab_version_of_a_beamline(RE, mappings):
    """
    Ensures that for every lab beamline all device factories are using valid args
    and creating types that conform to Bluesky protocols.
    """
    # todo patch the environment
    with patch.dict(os.environ, {"BEAMLINE": mappings[1]}):
        module = get_beamline_based_on_environment_variable()
        # get the devices file for the beamline namespace
        _, devices = get_module_name_by_beamline_name(mappings[0])
        for device_name, device in devices.items():
            assert device_name in beamline_utils.ACTIVE_DEVICES, (
                f"No device named {device_name} was created, devices "
                f"are {beamline_utils.ACTIVE_DEVICES.keys()}"
            )
            assert follows_bluesky_protocols(device)
        assert len(beamline_utils.ACTIVE_DEVICES) == len(devices)


@pytest.mark.parametrize(
    "module_and_devices_for_beamline",
    set(all_beamline_modules()),
    indirect=True,
)
def test_devices_are_identical(RE, module_and_devices_for_beamline):
    """
    Ensures that for every beamline all device functions prevent duplicate instantiation.
    """
    bl_mod, devices_a = module_and_devices_for_beamline
    devices_b, _ = make_all_devices(
        bl_mod,
        include_skipped=True,
        fake_with_ophyd_sim=True,
    )
    for device_name in devices_a.keys():
        assert devices_a[device_name] is devices_b[device_name]
