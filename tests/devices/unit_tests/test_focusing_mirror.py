import asyncio
from unittest.mock import DEFAULT, AsyncMock, patch

import pytest
from bluesky import FailedStatus, RunEngine
from bluesky import plan_stubs as bps
from ophyd_async.core import set_mock_value

from dodal.devices.focusing_mirror import (
    FocusingMirrorWithStripes,
    MirrorStripe,
    MirrorVoltageDemand,
    MirrorVoltageDevice,
    VFMMirrorVoltages,
)
from dodal.log import LOGGER


@pytest.fixture
def vfm_mirror_voltages_not_ok(vfm_mirror_voltages) -> VFMMirrorVoltages:
    set_mock_value(
        vfm_mirror_voltages.voltage_channels[0]._demand_accepted,
        MirrorVoltageDemand.FAIL,
    )
    return vfm_mirror_voltages


@pytest.fixture
def vfm_mirror_voltages_with_set(vfm_mirror_voltages) -> VFMMirrorVoltages:
    async def set_ok_after_delay():
        await asyncio.sleep(0.1)
        set_mock_value(
            vfm_mirror_voltages.voltage_channels[0]._demand_accepted,
            MirrorVoltageDemand.OK,
        )
        LOGGER.debug("DEMAND ACCEPTED OK")

    def not_ok_then_ok(_):
        set_mock_value(
            vfm_mirror_voltages.voltage_channels[0]._demand_accepted,
            MirrorVoltageDemand.SLEW,
        )
        asyncio.create_task(set_ok_after_delay())
        return DEFAULT

    vfm_mirror_voltages.voltage_channels[0]._setpoint_v.set = AsyncMock(
        side_effect=not_ok_then_ok
    )
    set_mock_value(
        vfm_mirror_voltages.voltage_channels[0]._demand_accepted,
        MirrorVoltageDemand.OK,
    )
    return vfm_mirror_voltages


@pytest.fixture
def vfm_mirror_voltages_with_set_timing_out(vfm_mirror_voltages) -> VFMMirrorVoltages:
    def not_ok(_):
        set_mock_value(
            vfm_mirror_voltages.voltage_channels[0]._demand_accepted,
            MirrorVoltageDemand.SLEW,
        )
        return DEFAULT

    vfm_mirror_voltages.voltage_channels[0]._setpoint_v.set = AsyncMock(
        side_effect=not_ok
    )
    set_mock_value(
        vfm_mirror_voltages.voltage_channels[0]._demand_accepted,
        MirrorVoltageDemand.OK,
    )
    return vfm_mirror_voltages


def test_mirror_set_voltage_sets_and_waits_happy_path(
    RE: RunEngine,
    vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    async def completed():
        pass

    vfm_mirror_voltages_with_set.voltage_channels[
        0
    ]._setpoint_v.set.return_value = completed()  # type: ignore
    set_mock_value(
        vfm_mirror_voltages_with_set.voltage_channels[0]._demand_accepted,
        MirrorVoltageDemand.OK,
    )

    def plan():
        yield from bps.abs_set(
            vfm_mirror_voltages_with_set.voltage_channels[0], 100, wait=True
        )

    RE(plan())

    vfm_mirror_voltages_with_set.voltage_channels[0]._setpoint_v.set.assert_called_with(  # type: ignore
        100
    )


def test_mirror_set_voltage_set_rejected_when_not_ok(
    RE: RunEngine,
    vfm_mirror_voltages_not_ok: VFMMirrorVoltages,
):
    def plan():
        with pytest.raises(FailedStatus) as e:
            yield from bps.abs_set(
                vfm_mirror_voltages_not_ok.voltage_channels[0], 100, wait=True
            )

        assert isinstance(e.value.args[0].exception(), AssertionError)

    RE(plan())


def test_mirror_set_voltage_sets_and_waits_set_fail(
    RE: RunEngine,
    vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    def failed(_):
        raise AssertionError("Test Failure")

    vfm_mirror_voltages_with_set.voltage_channels[
        0
    ]._setpoint_v.set.side_effect = failed  # type: ignore

    def plan():
        with pytest.raises(FailedStatus) as e:
            yield from bps.abs_set(
                vfm_mirror_voltages_with_set.voltage_channels[0], 100, wait=True
            )

        assert isinstance(e.value.args[0].exception(), AssertionError)

    RE(plan())


@patch("dodal.devices.focusing_mirror.DEFAULT_SETTLE_TIME_S", 3)
def test_mirror_set_voltage_sets_and_waits_settle_timeout_expires(
    RE: RunEngine,
    vfm_mirror_voltages_with_set_timing_out: VFMMirrorVoltages,
):
    def plan():
        with pytest.raises(Exception) as excinfo:
            yield from bps.abs_set(
                vfm_mirror_voltages_with_set_timing_out.voltage_channels[0],
                100,
                wait=True,
            )

        assert isinstance(excinfo.value.args[0].exception(), TimeoutError)

    RE(plan())


def test_mirror_set_voltage_returns_immediately_if_voltage_already_demanded(
    RE: RunEngine,
    vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    set_mock_value(vfm_mirror_voltages_with_set.voltage_channels[0]._setpoint_v, 100)

    def plan():
        yield from bps.abs_set(
            vfm_mirror_voltages_with_set.voltage_channels[0], 100, wait=True
        )

    RE(plan())

    vfm_mirror_voltages_with_set.voltage_channels[0]._setpoint_v.set.assert_not_called()  # type: ignore


def test_mirror_populates_voltage_channels(
    vfm_mirror_voltages_with_set: VFMMirrorVoltages,
):
    channels = vfm_mirror_voltages_with_set.voltage_channels
    assert len(channels) == 8
    assert isinstance(channels[0], MirrorVoltageDevice)


async def test_given_striped_focussing_mirror_then_energy_to_stripe_returns_expected():
    device = FocusingMirrorWithStripes(prefix="-OP-VFM-01:", name="mirror")
    await device.connect(mock=True)
    assert device.energy_to_stripe(1) == MirrorStripe.BARE
    assert device.energy_to_stripe(14) == MirrorStripe.RHODIUM
