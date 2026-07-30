import asyncio

import pytest
from ophyd_async.core import (
    DeviceMap,
    DeviceMock,
    StandardReadableFormat,
    default_mock_class,
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
    TemperatureSensor,
)


class MinimalMockSensor(BaseTemperatureSensor):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.sensor = epics_signal_r(float, prefix + "suffix")
        self.something_else = epics_signal_r(float, prefix + "suffix")
        super().__init__(name=name)


class MockHeater(BaseHeater):
    def __init__(self, name: str = ""):
        self.setpoint = epics_signal_rw(float, "prefix + suffix:SET")
        self.output = epics_signal_r(float, "prefix + suffix")
        super().__init__(name=name)


@default_mock_class(DeviceMock)
class MockTemperatureController(TemperatureController):
    def __init__(self, name: str = ""):
        sensor = TemperatureSensor[MinimalMockSensor](
            DeviceMap(
                {
                    "sensor1": MinimalMockSensor("prefix" + "STS:T1"),
                    "sensor2": MinimalMockSensor("prefix" + "STS:T2"),
                }
            )
        )
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


async def test_temperature_movable(
    mock_controller: MockTemperatureController,
):

    set_mock_value(mock_controller.tolerance, 0.5)
    set_mock_value(mock_controller.sensor.channel["sensor1"].sensor, 10.0)

    status = mock_controller.set(20.0)

    assert not status.done
    set_mock_value(mock_controller.sensor.channel["sensor1"].sensor, 19.8)
    await status
    assert status.done
    assert status.success


async def test_temperature_movable_with_different_sensor(
    mock_controller: MockTemperatureController,
):
    set_mock_value(mock_controller.tolerance, 0.2)
    await mock_controller.sensor.set("sensor2")
    status = mock_controller.set(18.8)
    assert not status.done
    set_mock_value(mock_controller.sensor.channel["sensor2"].sensor, 18.7)
    await status
    assert status.done
    assert status.success


async def test_temperature_controller_readback(
    mock_controller: MockTemperatureController,
):

    # await assert_reading(
    #     mock_controller,
    #     {
    #         "mock_controller-sensor-sensor1": partial_reading(0.0),
    #         "mock_controller-sensor-sensor2": partial_reading(0.0),
    #     },
    # )
    await assert_configuration(
        mock_controller,
        {
            "mock_controller-tolerance": partial_reading(0.1),
            "mock_controller-user_setpoint": partial_reading(0.0),
            "mock_controller-sensor-active_sensor_name": partial_reading("sensor1"),
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
    set_mock_value(mock_controller.sensor.channel["sensor1"].sensor, 0.5)
    await mock_controller.stop()
    assert await mock_controller.user_setpoint.get_value() == 0.5

    await mock_controller.sensor.set("sensor2")
    set_mock_value(mock_controller.sensor.channel["sensor2"].sensor, 8.8)
    set_mock_value(mock_controller.user_setpoint, 6.0)
    assert await mock_controller.user_setpoint.get_value() == 6.0
    await mock_controller.stop()
    assert await mock_controller.user_setpoint.get_value() == 8.8


async def test_temperature_controller_set_active_readback_with_invalid_sensor(
    mock_controller: MockTemperatureController,
):
    with pytest.raises(ValueError, match=r"\['sensor1', 'sensor2'\]"):
        await mock_controller.sensor.set_active_readback("sensor888")


async def test_temperature_controller_sensor_switch(
    mock_controller: MockTemperatureController,
):
    set_mock_value(mock_controller.sensor.channel["sensor2"].sensor, 2.0)
    # check defaulting to first sensor
    assert await mock_controller.sensor.active_sensor.get_value() == 0.0

    await mock_controller.sensor.set("sensor2")
    assert await mock_controller.sensor.active_sensor_name.get_value() == "sensor2"
    assert await mock_controller.sensor.active_sensor.get_value() == 2.0
    await mock_controller.sensor.set("sensor1")
    assert await mock_controller.sensor.active_sensor_name.get_value() == "sensor1"
    assert await mock_controller.sensor.active_sensor.get_value() == 0.0


async def test_sensor_switch_during_active_move(
    mock_controller: MockTemperatureController,
):
    set_mock_value(mock_controller.tolerance, 0.2)
    set_mock_value(mock_controller.sensor.channel["sensor1"].sensor, 10.0)
    set_mock_value(mock_controller.sensor.channel["sensor2"].sensor, 19.9)

    status = mock_controller.set(20.0)
    assert not status.done

    await mock_controller.sensor.set("sensor2")
    await status
    assert status.done
    assert status.success
    assert await mock_controller.sensor.active_sensor.get_value() == 19.9


async def test_temperature_sensor_fail_initiation_with_empty_map():
    with pytest.raises(
        ValueError,
        match=r"Cannot initialize TemperatureSensor with an empty DeviceMap.",
    ):
        TemperatureSensor(DeviceMap())
