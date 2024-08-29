from bluesky.run_engine import RunEngine
from ophyd_async.epics.motion.motor import Motor
from ophyd_async.plan_stubs.ensure_connected import ensure_connected

from dodal.common.beamlines.beamline_utils import ACTIVE_DEVICES
from dodal.common.beamlines.device_factory import (
    DeviceInitializationConfig,
    device_factory,
)


def test_terminal_use_case_decorated_motor_not_mock(RE: RunEngine):
    @device_factory()
    def motor(name: str = "motor", prefix: str = "motor:"):
        return Motor(name=name, prefix=prefix)

    m = motor(name="foo", mock=True)

    assert m is not None
    assert m.name == "foo"

    RE(ensure_connected(m))


def test_terminal_use_case_decorated_motor_mock(RE: RunEngine):
    @device_factory(mock=True)
    def motor(name: str = "motor", prefix: str = "motor:"):
        return Motor(name=name, prefix=prefix)

    m = motor()
    RE(ensure_connected(m))

    assert m is not None
    assert m.name == "motor"


def test_decorator_directly_with_name_override(RE: RunEngine):
    ACTIVE_DEVICES.clear()

    @device_factory(mock=True, use_factory_name=False)
    def m2():
        return Motor(name="foo", prefix="xyz:")

    device = m2()
    assert device is not None
    assert "foo" in ACTIVE_DEVICES.keys()


def test_decorator_directly_without_name_override(RE: RunEngine):
    ACTIVE_DEVICES.clear()

    @device_factory(mock=True)
    def m2():
        return Motor(name="foo", prefix="xyz:")

    device = m2()
    assert device is not None
    assert "m2" in ACTIVE_DEVICES.keys()


def test_custom_values():
    config = DeviceInitializationConfig(
        eager_connect=False,
        use_factory_name=False,
        timeout=5.0,
        mock=True,
        skip=True,
    )
    assert not config.eager_connect
    assert not config.use_factory_name
    assert config.timeout == 5.0
    assert config.mock
    assert config.skip


def test_config_with_lambda_skip():
    config = DeviceInitializationConfig(
        eager_connect=False,
        use_factory_name=False,
        timeout=5.0,
        mock=True,
        skip=lambda: True,
    )
    assert not config.eager_connect
    assert not config.use_factory_name
    assert config.timeout == 5.0
    assert config.mock
    assert config.skip


def test_device_caching(RE: RunEngine):
    beamline_prefix = "example:"

    @device_factory(mock=True)
    def my_motor():
        return Motor(prefix=f"{beamline_prefix}xyz:")

    ACTIVE_DEVICES.clear()

    d = my_motor()

    assert "my_motor" in ACTIVE_DEVICES
    assert ACTIVE_DEVICES["my_motor"] is d
