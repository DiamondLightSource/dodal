import asyncio

import pytest
from ophyd_async.core import (
    StandardReadableFormat,
    init_devices,
    set_mock_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.temperature_controller import (
    PID,
    BaseHeater,
    BaseTemperatureSensor,
    TemperatureController,
)


class MinimalMockSensor(BaseTemperatureSensor):
    def __init__(self, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.sensor = epics_signal_r(float, "prefix + suffix)")
            self.sensor2 = epics_signal_r(float, "prefix + suffix2)")
        self.sensor88 = 5
        super().__init__(name=name)


class MockHeater(BaseHeater):
    def __init__(self, name: str = ""):
        self.setpoint = epics_signal_rw(float, "prefix + suffix:SET")
        self.output = epics_signal_r(float, "prefix + suffix")
        super().__init__(name=name)


class MockTemperatureController(TemperatureController):
    def __init__(self, name: str = ""):
        sensor = MinimalMockSensor()
        heater = MockHeater()
        setpoint = epics_signal_rw(float, "prefix + suffix:SET")
        pid = PID(prefix="TEST-PID:")
        super().__init__(
            setpoint=setpoint,
            sensor=sensor,
            heater=heater,
            pid=pid,
            name=name,
        )


@pytest.fixture
def mock_controller() -> MockTemperatureController:
    with init_devices(mock=True):
        mock_controller = MockTemperatureController()
    return mock_controller


async def test_temperature_movable(mock_controller: MockTemperatureController):

    set_mock_value(mock_controller.tolerance, 0.5)
    set_mock_value(mock_controller.sensor.sensor, 10.0)

    status = mock_controller.set(20.0)
    assert not status.done
    set_mock_value(mock_controller.sensor.sensor, 19.4)

    assert not status.done
    set_mock_value(mock_controller.sensor.sensor, 19.8)
    await status
    assert status.done
    assert status.success


async def test_temperature_movable_with_different_sensor(
    mock_controller: MockTemperatureController,
):

    set_mock_value(mock_controller.tolerance, 0.5)
    set_mock_value(mock_controller.sensor.sensor, 10.0)

    status = mock_controller.set(20.0)
    assert not status.done
    set_mock_value(mock_controller.sensor.sensor, 19.4)

    assert not status.done
    set_mock_value(mock_controller.sensor.sensor, 19.8)
    await status
    assert status.done
    assert status.success
    await mock_controller.sensor.set("sensor2")
    status = mock_controller.set(18.8)
    assert not status.done
    set_mock_value(mock_controller.sensor.sensor2, 19.4)

    assert not status.done
    set_mock_value(mock_controller.sensor.sensor2, 18.7)
    await status
    assert status.done
    assert status.success


async def test_temperature_controller_readback(
    mock_controller: MockTemperatureController,
):
    await mock_controller.set(1.0)
    await assert_reading(
        mock_controller,
        {
            "mock_controller": partial_reading(1.0),
            "mock_controller-sensor-sensor2": partial_reading(0.0),
        },
    )
    await assert_configuration(
        mock_controller,
        {
            "mock_controller-tolerance": partial_reading(0.1),
            "mock_controller-user_setpoint": partial_reading(1.0),
        },
    )
    await asyncio.gather(
        mock_controller.pid.p.set(1.0),
        mock_controller.pid.i.set(2.0),
        mock_controller.pid.d.set(3.0),
    )
    await assert_reading(
        mock_controller.pid,
        {
            "mock_controller-pid-p": partial_reading(1.0),
            "mock_controller-pid-i": partial_reading(2.0),
            "mock_controller-pid-d": partial_reading(3.0),
        },
    )


async def test_temperature_controller_stop_with_different_sensor(
    mock_controller: MockTemperatureController,
):
    set_mock_value(mock_controller.user_setpoint, 1.0)
    set_mock_value(mock_controller.sensor.sensor, 0.5)
    await mock_controller.stop()
    assert await mock_controller.user_setpoint.get_value() == 0.5

    await mock_controller.sensor.set("sensor2")
    set_mock_value(mock_controller.sensor.sensor2, 8.8)
    set_mock_value(mock_controller.user_setpoint, 6.0)
    assert await mock_controller.user_setpoint.get_value() == 6.0
    await mock_controller.stop()
    assert await mock_controller.user_setpoint.get_value() == 8.8


async def test_temperature_controller_set_active_readback_with_invalid_sensor(
    mock_controller: MockTemperatureController,
):
    with pytest.raises(AttributeError):
        await mock_controller.sensor.set_active_readback("sensor888")

    with pytest.raises(TypeError):
        await mock_controller.sensor.set_active_readback("sensor88")
    with pytest.raises(ValueError):
        await mock_controller.sensor.set_active_readback("sensor8_1")
