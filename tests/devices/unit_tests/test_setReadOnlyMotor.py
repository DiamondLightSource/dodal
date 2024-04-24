import asyncio
from unittest.mock import ANY, Mock, call

import pytest
from ophyd_async.core import DeviceCollector
from ophyd_async.core.signal import set_sim_put_proceeds, set_sim_value

from dodal.devices.epics.setReadOnlyMotor import SetReadOnlyMotor

# Long enough for multiple asyncio event loop cycles to run so
# all the tasks have a chance to run
A_BIT = 0.001


@pytest.fixture
async def sim_sr_motor():
    async with DeviceCollector(sim=True):
        sim_sr_motor = SetReadOnlyMotor("BLxx-MO-xx-01:")
        # Signals connected here

    yield sim_sr_motor


async def test_setReadOnlyMotor_moves(sim_sr_motor: SetReadOnlyMotor) -> None:
    assert sim_sr_motor.name == "sim_sr_motor"
    set_sim_value(sim_sr_motor.motor_egu, "mm")

    set_sim_put_proceeds(sim_sr_motor.user_setpoint, False)
    s = sim_sr_motor.set(0.55)
    watcher = Mock()
    s.watch(watcher)
    done = Mock()
    s.add_callback(done)
    await asyncio.sleep(A_BIT)
    assert watcher.call_count == 1
    assert watcher.call_args == call(
        name="sim_sr_motor",
        current=0.0,
        initial=0.0,
        target=0.55,
        unit="mm",
        time_elapsed=ANY,
    )
    watcher.reset_mock()
    assert 0.55 == await sim_sr_motor.user_setpoint.get_value()
    assert not s.done
    await asyncio.sleep(0.1)
    set_sim_value(sim_sr_motor.user_readback, 0.1)
    assert watcher.call_count == 1
    assert watcher.call_args == call(
        name="sim_sr_motor",
        current=0.1,
        initial=0.0,
        target=0.55,
        unit="mm",
        time_elapsed=ANY,
    )
    sim_sr_motor._set_success = False  # make it fail
    set_sim_put_proceeds(sim_sr_motor.user_setpoint, True)
    await asyncio.sleep(A_BIT)
    assert s.done
    done.assert_called_once_with(s)


def test_motor_in_re(sim_sr_motor: SetReadOnlyMotor, RE) -> None:
    sim_sr_motor.move(0)

    def my_plan():
        yield sim_sr_motor.move(1)

    with pytest.raises(RuntimeError, match="Will deadlock run engine if run in a plan"):
        RE(my_plan())
