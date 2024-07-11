import asyncio

# prevent python 3.10 exception doppelganger stupidity
# see https://docs.python.org/3.10/library/asyncio-exceptions.html
# https://github.com/python/cpython/issues?q=is%3Aissue+timeouterror++alias+
from asyncio import TimeoutError
from unittest.mock import DEFAULT, patch

import pytest
from bluesky import FailedStatus, RunEngine
from bluesky import plan_stubs as bps
from ophyd_async.core import get_mock_put, set_mock_value

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
    return vfm_mirror_voltages_with_set_to_value(
        vfm_mirror_voltages, MirrorVoltageDemand.OK
    )


@pytest.fixture
def vfm_mirror_voltages_with_set_multiple_spins(
    vfm_mirror_voltages,
) -> VFMMirrorVoltages:
    return vfm_mirror_voltages_with_set_to_value(
        vfm_mirror_voltages, MirrorVoltageDemand.OK, 3
    )


@pytest.fixture
def vfm_mirror_voltages_with_set_accepted_fail(
    vfm_mirror_voltages,
) -> VFMMirrorVoltages:
    return vfm_mirror_voltages_with_set_to_value(
        vfm_mirror_voltages, MirrorVoltageDemand.FAIL
    )


def vfm_mirror_voltages_with_set_to_value(
    vfm_mirror_voltages, new_value: MirrorVoltageDemand, spins: int = 0
) -> VFMMirrorVoltages:
    async def set_demand_accepted_after_delay():
        await asyncio.sleep(0.1)
        nonlocal spins
        if spins > 0:
            set_mock_value(
                vfm_mirror_voltages.voltage_channels[0]._demand_accepted,
                MirrorVoltageDemand.SLEW,
            )
            spins -= 1
            asyncio.create_task(set_demand_accepted_after_delay())
        else:
            set_mock_value(
                vfm_mirror_voltages.voltage_channels[0]._demand_accepted,
                new_value,
            )
        LOGGER.debug("DEMAND ACCEPTED OK")

    def not_ok_then_other_value(*args, **kwargs):
        set_mock_value(
            vfm_mirror_voltages.voltage_channels[0]._demand_accepted,
            MirrorVoltageDemand.SLEW,
        )
        asyncio.create_task(set_demand_accepted_after_delay())
        return DEFAULT

    get_mock_put(
        vfm_mirror_voltages.voltage_channels[0]._setpoint_v
    ).side_effect = not_ok_then_other_value
    set_mock_value(
        vfm_mirror_voltages.voltage_channels[0]._demand_accepted,
        MirrorVoltageDemand.OK,
    )
    return vfm_mirror_voltages


@pytest.fixture
def vfm_mirror_voltages_with_set_timing_out(vfm_mirror_voltages) -> VFMMirrorVoltages:
    def not_ok(*args, **kwargs):
        set_mock_value(
            vfm_mirror_voltages.voltage_channels[0]._demand_accepted,
            MirrorVoltageDemand.SLEW,
        )
        return DEFAULT

    get_mock_put(
        vfm_mirror_voltages.voltage_channels[0]._setpoint_v
    ).side_effect = not_ok
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

    mock_put = get_mock_put(
        vfm_mirror_voltages_with_set.voltage_channels[0]._setpoint_v
    )
    mock_put.return_value = completed()
    set_mock_value(
        vfm_mirror_voltages_with_set.voltage_channels[0]._demand_accepted,
        MirrorVoltageDemand.OK,
    )

    def plan():
        yield from bps.abs_set(
            vfm_mirror_voltages_with_set.voltage_channels[0], 100, wait=True
        )

    RE(plan())

    mock_put.assert_called_with(100, wait=True, timeout=10.0)


def test_mirror_set_voltage_sets_and_waits_happy_path_spin_while_waiting_for_slew(
    RE: RunEngine,
    vfm_mirror_voltages_with_set_multiple_spins: VFMMirrorVoltages,
):
    async def completed():
        pass

    mock_put = get_mock_put(
        vfm_mirror_voltages_with_set_multiple_spins.voltage_channels[0]._setpoint_v
    )
    mock_put.return_value = completed()
    set_mock_value(
        vfm_mirror_voltages_with_set_multiple_spins.voltage_channels[
            0
        ]._demand_accepted,
        MirrorVoltageDemand.OK,
    )

    def plan():
        yield from bps.abs_set(
            vfm_mirror_voltages_with_set_multiple_spins.voltage_channels[0],
            100,
            wait=True,
        )

    RE(plan())

    mock_put.assert_called_with(100, wait=True, timeout=10.0)


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
    def failed(*args, **kwargs):
        raise AssertionError("Test Failure")

    get_mock_put(
        vfm_mirror_voltages_with_set.voltage_channels[0]._setpoint_v
    ).side_effect = failed

    def plan():
        with pytest.raises(FailedStatus) as e:
            yield from bps.abs_set(
                vfm_mirror_voltages_with_set.voltage_channels[0], 100, wait=True
            )

        assert isinstance(e.value.args[0].exception(), AssertionError)

    RE(plan())


def test_mirror_set_voltage_sets_and_waits_demand_accepted_fail(
    RE: RunEngine, vfm_mirror_voltages_with_set_accepted_fail
):
    def plan():
        with pytest.raises(FailedStatus) as e:
            yield from bps.abs_set(
                vfm_mirror_voltages_with_set_accepted_fail.voltage_channels[0],
                100,
                wait=True,
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

    get_mock_put(
        vfm_mirror_voltages_with_set.voltage_channels[0]._setpoint_v
    ).assert_not_called()


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
