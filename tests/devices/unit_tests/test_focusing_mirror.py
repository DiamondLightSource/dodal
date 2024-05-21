from threading import Timer
from unittest.mock import DEFAULT, MagicMock, patch

import pytest
from ophyd.sim import NullStatus
from ophyd.status import Status, StatusBase

from dodal.devices.focusing_mirror import (
    FocusingMirrorWithStripes,
    MirrorStripe,
    MirrorVoltageDemand,
    MirrorVoltageDevice,
    VFMMirrorVoltages,
)


@pytest.fixture
def mock_vfm_mirror_voltages_not_ok(mock_vfm_mirror_voltages) -> VFMMirrorVoltages:
    mock_vfm_mirror_voltages._channel14_voltage_device._demand_accepted.sim_put(
        MirrorVoltageDemand.FAIL
    )
    return mock_vfm_mirror_voltages


@pytest.fixture
def mock_vfm_mirror_voltages_with_set(mock_vfm_mirror_voltages) -> VFMMirrorVoltages:
    def not_ok_then_ok(_):
        mock_vfm_mirror_voltages._channel14_voltage_device._demand_accepted.sim_put(
            MirrorVoltageDemand.SLEW
        )
        Timer(
            0.1,
            lambda: mock_vfm_mirror_voltages._channel14_voltage_device._demand_accepted.sim_put(
                MirrorVoltageDemand.OK
            ),
        ).start()
        return DEFAULT

    mock_vfm_mirror_voltages._channel14_voltage_device._setpoint_v.set = MagicMock(
        side_effect=not_ok_then_ok
    )
    mock_vfm_mirror_voltages._channel14_voltage_device._demand_accepted.sim_put(
        MirrorVoltageDemand.OK
    )
    return mock_vfm_mirror_voltages


@pytest.fixture
def mock_vfm_mirror_voltages_with_set_timing_out(
    mock_vfm_mirror_voltages,
) -> VFMMirrorVoltages:
    def not_ok(_):
        mock_vfm_mirror_voltages._channel14_voltage_device._demand_accepted.sim_put(
            MirrorVoltageDemand.SLEW
        )
        return DEFAULT

    mock_vfm_mirror_voltages._channel14_voltage_device._setpoint_v.set = MagicMock(
        side_effect=not_ok
    )
    mock_vfm_mirror_voltages._channel14_voltage_device._demand_accepted.sim_put(
        MirrorVoltageDemand.OK
    )
    return mock_vfm_mirror_voltages


def test_mirror_set_voltage_sets_and_waits_happy_path(
    mock_vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    mock_vfm_mirror_voltages_with_set._channel14_voltage_device._setpoint_v.set.return_value = NullStatus()
    mock_vfm_mirror_voltages_with_set._channel14_voltage_device._demand_accepted.sim_put(
        MirrorVoltageDemand.OK
    )

    status: StatusBase = mock_vfm_mirror_voltages_with_set.voltage_channels[0].set(100)
    status.wait()
    mock_vfm_mirror_voltages_with_set._channel14_voltage_device._setpoint_v.set.assert_called_with(
        100
    )
    assert status.success


def test_mirror_set_voltage_set_rejected_when_not_ok(
    mock_vfm_mirror_voltages_not_ok: VFMMirrorVoltages,
):
    with pytest.raises(AssertionError):
        mock_vfm_mirror_voltages_not_ok.voltage_channels[0].set(100)


def test_mirror_set_voltage_sets_and_waits_set_fail(
    mock_vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    mock_vfm_mirror_voltages_with_set._channel14_voltage_device._setpoint_v.set.return_value = Status(
        success=False, done=True
    )

    status: StatusBase = mock_vfm_mirror_voltages_with_set.voltage_channels[0].set(100)
    with pytest.raises(Exception):
        status.wait()

    assert not status.success


@patch("dodal.devices.focusing_mirror.DEFAULT_SETTLE_TIME_S", 3)
def test_mirror_set_voltage_sets_and_waits_settle_timeout_expires(
    mock_vfm_mirror_voltages_with_set_timing_out: VFMMirrorVoltages,
):
    mock_vfm_mirror_voltages_with_set_timing_out._channel14_voltage_device._setpoint_v.set.return_value = NullStatus()

    status: StatusBase = mock_vfm_mirror_voltages_with_set_timing_out.voltage_channels[
        0
    ].set(100)

    with pytest.raises(Exception) as excinfo:
        status.wait()

    # Cannot assert because ophyd discards the original exception
    # assert isinstance(excinfo.value, WaitTimeoutError)
    assert excinfo.value


def test_mirror_set_voltage_returns_immediately_if_voltage_already_demanded(
    mock_vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    mock_vfm_mirror_voltages_with_set._channel14_voltage_device._setpoint_v.sim_put(100)

    status: StatusBase = mock_vfm_mirror_voltages_with_set.voltage_channels[0].set(100)
    status.wait()

    assert status.success
    mock_vfm_mirror_voltages_with_set._channel14_voltage_device._setpoint_v.set.assert_not_called()


def test_mirror_populates_voltage_channels(
    mock_vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    channels = mock_vfm_mirror_voltages_with_set.voltage_channels
    assert len(channels) == 8
    assert isinstance(channels[0], MirrorVoltageDevice)


async def test_given_striped_focussing_mirror_then_energy_to_stripe_returns_expected():
    device = FocusingMirrorWithStripes(prefix="-OP-VFM-01:", name="mirror")
    await device.connect(mock=True)
    assert device.energy_to_stripe(1) == MirrorStripe.BARE
    assert device.energy_to_stripe(14) == MirrorStripe.RHODIUM
