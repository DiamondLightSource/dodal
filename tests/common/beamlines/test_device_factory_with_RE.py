from bluesky.run_engine import RunEngine
from ophyd_async.epics.motion.motor import Motor
from ophyd_async.plan_stubs.ensure_connected import ensure_connected

from dodal.common.beamlines.device_factory import (
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
