from unittest.mock import MagicMock, patch

import pytest
from ophyd.sim import NullStatus
from ophyd.status import Status, StatusBase

from dodal.devices.focusing_mirror import (
    DEMAND_ACCEPTED_OK,
    MirrorVoltageDevice,
    VFMMirrorVoltages,
)


@pytest.fixture
def vfm_mirror_voltages_with_set(vfm_mirror_voltages) -> VFMMirrorVoltages:
    vfm_mirror_voltages._channel14_voltage_device._setpoint_v.set = MagicMock()
    return vfm_mirror_voltages


def test_mirror_set_voltage_sets_and_waits_happy_path(
    vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    vfm_mirror_voltages_with_set._channel14_voltage_device._setpoint_v.set.return_value = (
        NullStatus()
    )
    vfm_mirror_voltages_with_set._channel14_voltage_device._demand_accepted.sim_put(
        DEMAND_ACCEPTED_OK
    )

    status: StatusBase = vfm_mirror_voltages_with_set.voltage_channels[0].set(100)
    status.wait()
    vfm_mirror_voltages_with_set._channel14_voltage_device._setpoint_v.set.assert_called_with(
        100
    )
    assert status.success


def test_mirror_set_voltage_sets_and_waits_set_fail(
    vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    vfm_mirror_voltages_with_set._channel14_voltage_device._setpoint_v.set.return_value = Status(
        success=False, done=True
    )

    status: StatusBase = vfm_mirror_voltages_with_set.voltage_channels[0].set(100)
    try:
        status.wait()
    except Exception:
        pass

    assert not status.success


@patch("dodal.devices.focusing_mirror.DEFAULT_SETTLE_TIME_S", 3)
def test_mirror_set_voltage_sets_and_waits_settle_timeout_expires(
    vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    vfm_mirror_voltages_with_set._channel14_voltage_device._setpoint_v.set.return_value = (
        NullStatus()
    )
    vfm_mirror_voltages_with_set._channel14_voltage_device._demand_accepted.sim_put(0)

    status: StatusBase = vfm_mirror_voltages_with_set.voltage_channels[0].set(100)

    actual_exception = None
    try:
        status.wait()
    except Exception as e:
        actual_exception = e

    # Cannot assert because ophyd discards the original exception
    # assert isinstance(actual_exception, WaitTimeoutError)
    assert actual_exception


def test_mirror_set_voltage_returns_immediately_if_voltage_already_demanded(
    vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    vfm_mirror_voltages_with_set._channel14_voltage_device._setpoint_v.sim_put(100)

    status: StatusBase = vfm_mirror_voltages_with_set.voltage_channels[0].set(100)
    status.wait()

    assert status.success
    vfm_mirror_voltages_with_set._channel14_voltage_device._setpoint_v.set.assert_not_called()


def test_mirror_populates_voltage_channels(
    vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    channels = vfm_mirror_voltages_with_set.voltage_channels
    assert len(channels) == 8
    assert isinstance(channels[0], MirrorVoltageDevice)
