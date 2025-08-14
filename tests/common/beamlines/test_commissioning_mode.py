import pytest
from bluesky import RunEngine
from bluesky.utils import MsgGenerator
from ophyd_async.testing import set_mock_value

from dodal.common.beamlines.commissioning_mode import read_commissioning_mode
from dodal.devices.baton import Baton


@pytest.mark.parametrize("mode", [True, False])
def test_read_commissioning_mode_returns_signal_status_when_signal_registered(
    RE: RunEngine, baton_in_commissioning_mode: Baton, mode: bool
):
    actual_mode = False

    def check_commissioning_mode() -> MsgGenerator:
        nonlocal actual_mode
        actual_mode = yield from read_commissioning_mode()

    set_mock_value(baton_in_commissioning_mode.commissioning, mode)
    RE(check_commissioning_mode())
    assert actual_mode == mode


def test_read_commissioning_mode_returns_false_when_no_signal_registered(
    RE: RunEngine,
):
    actual_mode = False

    def check_commissioning_mode() -> MsgGenerator:
        nonlocal actual_mode
        actual_mode = yield from read_commissioning_mode()

    RE(check_commissioning_mode())
    assert not actual_mode
