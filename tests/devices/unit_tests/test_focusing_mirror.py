from unittest.mock import MagicMock, patch

import pytest
from ophyd.sim import NullStatus, make_fake_device
from ophyd.status import Status

from dodal.devices.focusing_mirror import (
    DEMAND_ACCEPTED_OK,
    FocusingMirror,
    MirrorVoltageSignal,
    VFMMirrorVoltages,
)


@pytest.fixture
def vfm() -> FocusingMirror:
    mirror: FocusingMirror = make_fake_device(FocusingMirror)
    return mirror


@pytest.fixture
def vfm_mirror_voltages() -> VFMMirrorVoltages:
    mirror: VFMMirrorVoltages = make_fake_device(VFMMirrorVoltages)(
        name="vfm_mirror_voltages"
    )
    mirror._channel14_setpoint_v.set = MagicMock()
    return mirror


def test_mirror_set_voltage_sets_and_waits_happy_path(
    vfm_mirror_voltages: VFMMirrorVoltages,
):
    vfm_mirror_voltages._channel14_setpoint_v.set.return_value = NullStatus()
    vfm_mirror_voltages._channel14_demand_accepted.sim_put(DEMAND_ACCEPTED_OK)

    status: Status = vfm_mirror_voltages.channel14.set(100)
    status.wait()
    vfm_mirror_voltages._channel14_setpoint_v.set.assert_called_with(100)
    assert status.success


def test_mirror_set_voltage_sets_and_waits_set_fail(
    vfm_mirror_voltages: VFMMirrorVoltages,
):
    vfm_mirror_voltages._channel14_setpoint_v.set.return_value = Status(
        success=False, done=True
    )

    status: Status = vfm_mirror_voltages.channel14.set(100)
    try:
        status.wait()
    except Exception:
        pass

    assert not status.success


@patch("dodal.devices.focusing_mirror.DEFAULT_SETTLE_TIME_S", 3)
def test_mirror_set_voltage_sets_and_waits_settle_timeout_expires(
    vfm_mirror_voltages: VFMMirrorVoltages,
):
    vfm_mirror_voltages._channel14_setpoint_v.set.return_value = NullStatus()
    vfm_mirror_voltages._channel14_demand_accepted.sim_put(0)

    status: Status = vfm_mirror_voltages.channel14.set(100)

    actual_exception = None
    try:
        status.wait()
    except Exception as e:
        actual_exception = e

    # Cannot assert because ophyd discards the original exception
    # assert isinstance(actual_exception, WaitTimeoutError)
    assert actual_exception


def test_mirror_populates_voltage_channels(vfm_mirror_voltages: VFMMirrorVoltages):
    channels = vfm_mirror_voltages.voltage_channels
    assert len(channels) == 8
    assert isinstance(channels[0], MirrorVoltageSignal)
