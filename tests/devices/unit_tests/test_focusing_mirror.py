import asyncio

# prevent python 3.10 exception doppelganger stupidity
# see https://docs.python.org/3.10/library/asyncio-exceptions.html
# https://github.com/python/cpython/issues?q=is%3Aissue+timeouterror++alias+
from asyncio import TimeoutError
from unittest.mock import ANY, DEFAULT, patch

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.focusing_mirror import (
    FocusingMirrorWithStripes,
    MirrorStripe,
    MirrorStripeConfiguration,
    MirrorVoltageDemand,
    MirrorVoltages,
    SingleMirrorVoltage,
)
from dodal.log import LOGGER


def mirror_voltage_with_set_to_value(
    mirror_voltage: SingleMirrorVoltage, new_value: MirrorVoltageDemand, spins: int = 0
) -> SingleMirrorVoltage:
    async def set_demand_accepted_after_delay():
        await asyncio.sleep(0.1)
        nonlocal spins
        if spins > 0:
            set_mock_value(
                mirror_voltage._demand_accepted,
                MirrorVoltageDemand.SLEW,
            )
            spins -= 1
            asyncio.create_task(set_demand_accepted_after_delay())
        else:
            set_mock_value(
                mirror_voltage._demand_accepted,
                new_value,
            )
        LOGGER.debug("DEMAND ACCEPTED OK")

    def not_ok_then_other_value(*args, **kwargs):
        set_mock_value(
            mirror_voltage._demand_accepted,
            MirrorVoltageDemand.SLEW,
        )
        asyncio.create_task(set_demand_accepted_after_delay())
        return DEFAULT

    callback_on_mock_put(mirror_voltage._setpoint_v, not_ok_then_other_value)
    set_mock_value(
        mirror_voltage._demand_accepted,
        MirrorVoltageDemand.OK,
    )
    return mirror_voltage


@pytest.fixture
def mirror_voltage():
    with init_devices(mock=True):
        mirror_voltage = SingleMirrorVoltage()
    return mirror_voltage


@pytest.fixture
def mirror_voltage_with_set(
    mirror_voltage: SingleMirrorVoltage,
) -> SingleMirrorVoltage:
    return mirror_voltage_with_set_to_value(mirror_voltage, MirrorVoltageDemand.OK)


@pytest.fixture
def mirror_voltage_not_ok(mirror_voltage: SingleMirrorVoltage) -> SingleMirrorVoltage:
    set_mock_value(mirror_voltage._demand_accepted, MirrorVoltageDemand.FAIL)
    return mirror_voltage


@pytest.fixture
def mirror_voltage_with_set_multiple_spins(
    mirror_voltage: SingleMirrorVoltage,
) -> SingleMirrorVoltage:
    return mirror_voltage_with_set_to_value(mirror_voltage, MirrorVoltageDemand.OK, 3)


@pytest.fixture
def mirror_voltage_with_set_accepted_fail(
    mirror_voltage: SingleMirrorVoltage,
) -> SingleMirrorVoltage:
    return mirror_voltage_with_set_to_value(mirror_voltage, MirrorVoltageDemand.FAIL)


@pytest.fixture
def mirror_voltage_with_set_timing_out(
    mirror_voltage: SingleMirrorVoltage,
) -> SingleMirrorVoltage:
    def not_ok(*args, **kwargs):
        set_mock_value(
            mirror_voltage._demand_accepted,
            MirrorVoltageDemand.SLEW,
        )
        return DEFAULT

    get_mock_put(mirror_voltage._setpoint_v).side_effect = not_ok
    set_mock_value(
        mirror_voltage._demand_accepted,
        MirrorVoltageDemand.OK,
    )
    return mirror_voltage


def test_mirror_set_voltage_sets_and_waits_happy_path(
    RE: RunEngine,
    mirror_voltage_with_set: SingleMirrorVoltage,
):
    def completed():
        pass

    mock_put = get_mock_put(mirror_voltage_with_set._setpoint_v)
    mock_put.return_value = completed()
    set_mock_value(
        mirror_voltage_with_set._demand_accepted,
        MirrorVoltageDemand.OK,
    )

    def plan():
        yield from bps.abs_set(mirror_voltage_with_set, 100, wait=True)

    RE(plan())

    mock_put.assert_called_with(100, wait=ANY)


def test_mirror_set_voltage_sets_and_waits_happy_path_spin_while_waiting_for_slew(
    RE: RunEngine,
    mirror_voltage_with_set_multiple_spins: SingleMirrorVoltage,
):
    def completed():
        pass

    mock_put = get_mock_put(mirror_voltage_with_set_multiple_spins._setpoint_v)
    mock_put.return_value = completed()
    set_mock_value(
        mirror_voltage_with_set_multiple_spins._demand_accepted,
        MirrorVoltageDemand.OK,
    )

    def plan():
        yield from bps.abs_set(
            mirror_voltage_with_set_multiple_spins,
            100,
            wait=True,
        )

    RE(plan())

    mock_put.assert_called_with(100, wait=ANY)


def test_mirror_set_voltage_set_rejected_when_not_ok(
    RE: RunEngine,
    mirror_voltage_not_ok: SingleMirrorVoltage,
):
    def plan():
        with pytest.raises(FailedStatus) as e:
            yield from bps.abs_set(mirror_voltage_not_ok, 100, wait=True)

        assert isinstance(e.value.args[0].exception(), AssertionError)

    RE(plan())


def test_mirror_set_voltage_sets_and_waits_set_fail(
    RE: RunEngine,
    mirror_voltage_with_set: SingleMirrorVoltage,
):
    def failed(*args, **kwargs):
        raise AssertionError("Test Failure")

    mirror_voltage_with_set._setpoint_v.set = failed

    def plan():
        with pytest.raises(FailedStatus) as e:
            yield from bps.abs_set(mirror_voltage_with_set, 100, wait=True)

        assert isinstance(e.value.args[0].exception(), AssertionError)

    RE(plan())


def test_mirror_set_voltage_sets_and_waits_demand_accepted_fail(
    RE: RunEngine, mirror_voltage_with_set_accepted_fail: SingleMirrorVoltage
):
    def plan():
        with pytest.raises(FailedStatus) as e:
            yield from bps.abs_set(
                mirror_voltage_with_set_accepted_fail,
                100,
                wait=True,
            )

        assert isinstance(e.value.args[0].exception(), AssertionError)

    RE(plan())


@patch("dodal.devices.focusing_mirror.DEFAULT_SETTLE_TIME_S", 0.1)
def test_mirror_set_voltage_sets_and_waits_settle_timeout_expires(
    RE: RunEngine,
    mirror_voltage_with_set_timing_out: SingleMirrorVoltage,
):
    def plan():
        with pytest.raises(Exception) as excinfo:
            yield from bps.abs_set(
                mirror_voltage_with_set_timing_out,
                100,
                wait=True,
            )
        assert isinstance(excinfo.value.args[0].exception(), TimeoutError)

    RE(plan())


def test_mirror_set_voltage_returns_immediately_if_voltage_already_demanded(
    RE: RunEngine,
    mirror_voltage_with_set: SingleMirrorVoltage,
):
    set_mock_value(mirror_voltage_with_set._setpoint_v, 100)

    def plan():
        yield from bps.abs_set(mirror_voltage_with_set, 100, wait=True)

    RE(plan())

    get_mock_put(mirror_voltage_with_set._setpoint_v).assert_not_called()


def test_mirror_populates_voltage_channels(RE):
    with init_devices(mock=True):
        mirror_voltages = MirrorVoltages("", "", daq_configuration_path="")
    assert len(mirror_voltages.horizontal_voltages) == 14
    assert len(mirror_voltages.vertical_voltages) == 8
    assert isinstance(mirror_voltages.horizontal_voltages[0], SingleMirrorVoltage)


@pytest.mark.parametrize(
    "energy_kev, expected_config",
    [
        [1, {"stripe": MirrorStripe.BARE, "yaw_mrad": 6.2, "lat_mm": 0.0}],
        [14, {"stripe": MirrorStripe.RHODIUM, "yaw_mrad": 0.0, "lat_mm": 10.0}],
    ],
)
async def test_given_striped_focussing_mirror_then_energy_to_stripe_returns_expected(
    RE, energy_kev: float, expected_config: MirrorStripeConfiguration
):
    with init_devices(mock=True):
        device = FocusingMirrorWithStripes(prefix="-OP-VFM-01:", name="mirror")
    assert device.energy_to_stripe(energy_kev) == expected_config
