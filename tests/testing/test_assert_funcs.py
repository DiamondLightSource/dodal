from unittest.mock import patch

import pytest
from bluesky import RunEngine
from bluesky.utils import MsgGenerator
from ophyd_async.core import Device, init_devices
from ophyd_async.epics.motor import Motor

from dodal.common import inject
from dodal.testing import (
    assert_plan_has_valid_inject_devices_for_beamline,
    find_inject_args,
)


def plan_with_device_on_beamline(test: Device = inject("device_on_bl")) -> MsgGenerator:  # noqa: B008
    yield from {}


def plan_with_device_not_on_beamline(
    test: Device = inject("invalid_device"),  # noqa: B008
) -> MsgGenerator:
    yield from {}


def test_find_inject_args_with_one_():
    assert ["device_on_bl"] == find_inject_args(plan_with_device_on_beamline)


@pytest.fixture
def device_on_bl(RE: RunEngine) -> Motor:
    with init_devices(mock=True, connect=False):
        device_on_bl = Motor("TEST:")
    return device_on_bl


def test_assert_plan_has_valid_inject_devices_for_beamline(device_on_bl: Motor):
    with patch(
        "dodal.testing.assert_funcs.make_all_devices",
        return_value=({device_on_bl.name: device_on_bl}, {}),
    ):
        assert_plan_has_valid_inject_devices_for_beamline(
            "iXX", plan_with_device_on_beamline
        )


def test_assert_plan_has_invalid_inject_devices_for_beamline(device_on_bl: Motor):
    with patch(
        "dodal.testing.assert_funcs.make_all_devices",
        return_value=({device_on_bl.name: device_on_bl}, {}),
    ):
        with pytest.raises(AssertionError):
            assert_plan_has_valid_inject_devices_for_beamline(
                "iXX", plan_with_device_not_on_beamline
            )
