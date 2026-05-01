from typing import Any

import pytest
from daq_config_server import ConfigClient
from ophyd_async.core import NotConnectedError

from dodal.beamlines import all_beamline_modules
from dodal.common.beamlines.beamline_utils import clear_config_client, set_config_client
from dodal.utils import BLUESKY_PROTOCOLS
from tests.test_data import I04_BEAMLINE_PARAMETERS, TEST_BEAMLINE_PARAMETERS_TXT


def follows_bluesky_protocols(obj: Any) -> bool:
    return any(isinstance(obj, protocol) for protocol in BLUESKY_PROTOCOLS)


@pytest.fixture(autouse=True)
def patch_config_paths(monkeypatch):
    monkeypatch.setattr(
        "dodal.beamlines.i03.BEAMLINE_PARAMETERS_PATH",
        TEST_BEAMLINE_PARAMETERS_TXT,
    )
    monkeypatch.setattr(
        "dodal.beamlines.i04.BEAMLINE_PARAMETERS_PATH",
        I04_BEAMLINE_PARAMETERS,
    )


@pytest.fixture(autouse=True)
def reset_config_client():
    set_config_client(ConfigClient(""))
    yield
    clear_config_client()


@pytest.mark.parametrize(
    "module_and_devices_for_beamline",
    set(all_beamline_modules()),
    indirect=True,
)
def test_device_creation(module_and_devices_for_beamline):
    """Ensures that for every beamline all device factories are using valid args
    and creating types that conform to Bluesky protocols.
    """
    _, devices, exceptions = module_and_devices_for_beamline
    if len(exceptions) > 0:
        raise NotConnectedError(exceptions)
    devices_not_following_bluesky_protocols = [
        name
        for name, device in devices.items()
        if not follows_bluesky_protocols(device)
    ]
    assert len(devices_not_following_bluesky_protocols) == 0, (
        f"{devices_not_following_bluesky_protocols} do not follow bluesky protocols"
    )
