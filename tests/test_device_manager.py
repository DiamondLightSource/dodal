from ophyd_async.sim import SimMotor
import pytest
from pytest import RaisesExc, RaisesGroup
from unittest.mock import Mock

from ophyd_async.core import Device as OphydV2Device

from dodal.device_manager import DeviceManager


def test_single_factory():
    dm = DeviceManager()

    s1 = Mock()

    @dm.factory
    def sim() -> OphydV2Device:
        return s1()

    devices = dm.build_all()
    s1.assert_called_once()
    assert devices.devices == {"sim": s1()}


def test_two_devices():
    dm = DeviceManager()

    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo():
        return s1()

    @dm.factory
    def bar():
        return s2()

    devices = dm.build_all()
    s1.assert_called_once()
    s2.assert_called_once()
    assert devices.devices == {"foo": s1(), "bar": s2()}


def test_build_one_of_two():
    dm = DeviceManager()

    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo():
        return s1()

    @dm.factory
    def bar():
        return s2()

    devices = dm.build_devices(foo)
    s1.assert_called_once()
    s2.assert_not_called()
    assert devices.devices == {"foo": s1()}


def test_build_directly():
    dm = DeviceManager()

    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo():
        return s1()

    @dm.factory
    def bar():
        return s2()

    f = foo()
    s1.assert_called_once()
    s2.assert_not_called()
    assert f == s1()


def test_build_method():
    dm = DeviceManager()

    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo():
        return s1()

    @dm.factory
    def bar():
        return s2()

    f = foo.build()
    s1.assert_called_once()
    s2.assert_not_called()
    assert f == s1()


def test_dependent_devices():
    dm = DeviceManager()

    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo(bar):
        return s1(bar)

    @dm.factory
    def bar():
        return s2()

    devices = dm.build_all()
    s2.assert_called_once()
    s1.assert_called_once_with(s2())

    assert devices.devices == {"foo": s1(s2()), "bar": s2()}


def test_dependent_device_build_method():
    dm = DeviceManager()

    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo(bar):
        return s1(bar)

    @dm.factory
    def bar():
        return s2()

    f = foo.build()
    s2.assert_called_once()
    s1.assert_called_once_with(s2())

    assert f == s1(s2())


def test_fixture_argument():
    dm = DeviceManager()

    s1 = Mock()

    @dm.factory
    def foo(bar):
        return s1(bar)

    dm.build_all(fixtures={"bar": 123})
    s1.assert_called_once_with(123)


def test_none_fixture():
    dm = DeviceManager()

    s1 = Mock()

    @dm.factory
    def foo(bar):
        return s1(bar)

    devices = dm.build_all(fixtures={"bar": None})
    s1.assert_called_once_with(None)
    assert devices.devices == {"foo": s1(None)}


def test_default_argument():
    dm = DeviceManager()

    s1 = Mock()

    @dm.factory
    def foo(bar=42):
        return s1(bar)

    dm.build_all()
    s1.assert_called_once_with(42)


def test_fixture_overrides_default_argument():
    dm = DeviceManager()

    s1 = Mock()

    @dm.factory
    def foo(bar=42):
        return s1(bar)

    dm.build_all(fixtures={"bar": 17})
    s1.assert_called_once_with(17)


def test_fixture_overrides_factory():
    dm = DeviceManager()

    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo(bar):
        return s1(bar)

    @dm.factory
    def bar():
        return s2()

    devices = dm.build_all(fixtures={"bar": 17})
    s1.assert_called_once_with(17)
    s2.assert_not_called()

    assert devices.devices == {"foo": s1(17), "bar": 17}


def test_fixture_function():
    dm = DeviceManager()

    s1 = Mock()

    @dm.factory
    def foo(bar=42):
        return s1(bar)

    @dm.fixture
    def bar():
        return 42

    devices = dm.build_all()
    s1.assert_called_once_with(42)
    assert devices.devices == {"foo": s1(42)}


def test_fixture_functions_are_lazy():
    dm = DeviceManager()

    s1 = Mock()
    fix = Mock()
    fix.__name__ = "fix"
    dm.fixture(fix)

    @dm.factory
    def foo():
        return s1()

    devices = dm.build_all()
    s1.assert_called_once()
    fix.assert_not_called()
    assert devices.devices == {"foo": s1()}


def test_duplicate_factories_error():
    dm = DeviceManager()

    s1 = Mock()

    @dm.factory
    def foo():
        return s1()

    with pytest.raises(ValueError):

        @dm.factory
        def foo():
            return s1()


def test_missing_dependency_errors():
    dm = DeviceManager()
    s1 = Mock()

    @dm.factory
    def foo(bar):
        return s1()

    with pytest.raises(ValueError, match="Missing fixture or factory for bar"):
        dm.build_all()


def test_missing_fixture_ok_if_not_required():
    dm = DeviceManager()

    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo(unknown):
        return s1(bar)

    @dm.factory
    def bar():
        return s2()

    # missing unknown but not needed for bar so ok
    devices = dm.build_devices(bar)

    s1.assert_not_called()
    assert devices.devices == {"bar": s2()}


def test_circular_dependencies_error():
    dm = DeviceManager()

    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo(bar):
        return s1(bar)

    @dm.factory
    def bar(foo):
        return s2(foo)

    with pytest.raises(ValueError, match="circular dependencies"):
        dm.build_all()


# chasing coverage numbers
def test_repr():
    dm = DeviceManager()
    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo(bar: int) -> SimMotor:
        return s1(bar)

    @dm.factory
    def bar(foo):
        return s2(foo)

    assert repr(dm) == "<DeviceManager: 2 devices>"
    assert (
        repr(foo) == "<foo: DeviceFactory(bar: int) -> ophyd_async.sim._motor.SimMotor>"
    )


def test_build_errors_are_caught():
    dm = DeviceManager()
    s1 = Mock()
    err = RuntimeError("Build failed")
    s1.side_effect = err

    @dm.factory
    def foo():
        return s1()

    devices = dm.build_all()

    s1.assert_called_once()
    assert devices.devices == {}
    assert devices.errors == {"foo": err}


def test_dependency_errors_propagate():
    dm = DeviceManager()

    s1 = Mock()
    err = RuntimeError("Build failed")
    s2 = Mock()
    s2.side_effect = err

    @dm.factory
    def foo(bar):
        return s1(bar)

    @dm.factory
    def bar():
        return s2()

    devices = dm.build_all()
    s2.assert_called_once()
    s1.assert_not_called()

    assert devices.devices == {}
    assert devices.errors["bar"] == err
    foo_err = devices.errors["foo"]
    assert isinstance(foo_err, ValueError)
    assert foo_err.args == ("Errors building dependencies: {'bar'}",)


def test_devices_are_named():
    dm = DeviceManager()
    s1 = Mock()

    @dm.factory
    def foo():
        return s1()

    f = foo.build()

    s1.assert_called_once()
    f.set_name.assert_called_once_with("foo")


def test_skip_naming():
    dm = DeviceManager()
    s1 = Mock()

    @dm.factory(use_factory_name=False)
    def foo():
        return s1()

    f = foo.build()

    s1.assert_called_once()
    f.set_name.assert_not_called()


def test_override_name():
    dm = DeviceManager()
    s1 = Mock()

    @dm.factory
    def foo():
        return s1()

    f = foo.build(name="not_foo")

    s1.assert_called_once()
    f.set_name.assert_called_with("not_foo")


def test_positional_only_args_error():
    dm = DeviceManager()
    s1 = Mock()

    with pytest.raises(ValueError, match="positional only arguments"):

        @dm.factory
        def foo(foo, /):
            return s1()


def test_devices_or_raise():
    dm = DeviceManager()
    s1 = Mock()
    s1.side_effect = RuntimeError("Build failed")

    @dm.factory
    def foo():
        return s1()

    devices = dm.build_all()
    with RaisesGroup(RaisesExc(RuntimeError, match="Build failed")):
        devices.or_raise()
