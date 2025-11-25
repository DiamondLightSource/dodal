from unittest.mock import MagicMock, Mock, patch

import pytest
from ophyd.device import Device as OphydV1Device
from ophyd_async.core import Device as OphydV2Device
from ophyd_async.sim import SimMotor
from pytest import RaisesExc, RaisesGroup

from dodal.device_manager import (
    DEFAULT_TIMEOUT,
    DeviceBuildResult,
    DeviceManager,
    LazyFixtures,
)


@pytest.fixture
def dm() -> DeviceManager:
    return DeviceManager()


def test_single_factory(dm: DeviceManager):
    s1 = Mock()

    @dm.factory
    def sim() -> OphydV2Device:
        return s1()

    devices = dm.build_all()
    s1.assert_called_once()
    assert devices.devices == {"sim": s1()}


def test_two_devices(dm: DeviceManager):
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


def test_build_one_of_two(dm: DeviceManager):
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


def test_build_directly(dm: DeviceManager):
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


def test_build_method(dm: DeviceManager):
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


def test_dependent_devices(dm: DeviceManager):
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


def test_dependent_device_build_method(dm: DeviceManager):
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


def test_fixture_argument(dm: DeviceManager):
    s1 = Mock()

    @dm.factory
    def foo(bar):
        return s1(bar)

    dm.build_all(fixtures={"bar": 123})
    s1.assert_called_once_with(123)


def test_none_fixture(dm: DeviceManager):
    s1 = Mock()

    @dm.factory
    def foo(bar):
        return s1(bar)

    devices = dm.build_all(fixtures={"bar": None})
    s1.assert_called_once_with(None)
    assert devices.devices == {"foo": s1(None)}


def test_default_argument(dm: DeviceManager):
    s1 = Mock()

    @dm.factory
    def foo(bar=42):
        return s1(bar)

    dm.build_all()
    s1.assert_called_once_with(42)


def test_fixture_overrides_default_argument(dm: DeviceManager):
    s1 = Mock()

    @dm.factory
    def foo(bar=42):
        return s1(bar)

    dm.build_all(fixtures={"bar": 17})
    s1.assert_called_once_with(17)


def test_fixture_overrides_factory(dm: DeviceManager):
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


def test_fixture_function(dm: DeviceManager):
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


def test_fixture_functions_are_lazy(dm: DeviceManager):
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


def test_duplicate_factories_error(dm: DeviceManager):
    s1 = Mock()

    @dm.factory
    def foo():
        return s1()

    with pytest.raises(ValueError):

        @dm.factory
        def foo():
            return s1()


def test_missing_dependency_errors(dm: DeviceManager):
    s1 = Mock()

    @dm.factory
    def foo(bar):
        return s1()

    with pytest.raises(ValueError, match="Missing fixture or factory for bar"):
        dm.build_all()


def test_missing_fixture_ok_if_not_required(dm: DeviceManager):
    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo(unknown):
        return s1(unknown)

    @dm.factory
    def bar():
        return s2()

    # missing unknown but not needed for bar so ok
    devices = dm.build_devices(bar)

    s1.assert_not_called()
    assert devices.devices == {"bar": s2()}


def test_circular_dependencies_error(dm: DeviceManager):
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
def test_repr(dm: DeviceManager):
    s1 = Mock()
    s2: type[OphydV1Device] = Mock()  # type: ignore
    s2.__name__ = "S2"

    @dm.factory
    def foo(one: int) -> SimMotor:
        return s1(one)

    @dm.v1_init(s2, prefix="S2_PREFIX")
    def bar(_):
        pass

    assert repr(dm) == "<DeviceManager: 2 devices>"
    assert (
        repr(foo) == "<foo: DeviceFactory(one: int) -> ophyd_async.sim._motor.SimMotor>"
    )
    assert repr(bar) == "<bar: V1DeviceFactory[S2]>"


def test_build_errors_are_caught(dm: DeviceManager):
    err = RuntimeError("Build failed")
    s1 = Mock(side_effect=err)

    @dm.factory
    def foo():
        return s1()

    devices = dm.build_all()

    s1.assert_called_once()
    assert devices.devices == {}
    assert devices.errors == {"foo": err}


def test_dependency_errors_propagate(dm: DeviceManager):
    s1 = Mock()
    err = RuntimeError("Build failed")
    s2 = Mock(side_effect=err)

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


def test_devices_are_named(dm: DeviceManager):
    s1 = Mock()

    @dm.factory
    def foo():
        return s1()

    f = foo.build()

    s1.assert_called_once()
    f.set_name.assert_called_once_with("foo")


def test_skip_naming(dm: DeviceManager):
    s1 = Mock()

    @dm.factory(use_factory_name=False)
    def foo():
        return s1()

    f = foo.build()

    s1.assert_called_once()
    f.set_name.assert_not_called()


def test_override_name(dm: DeviceManager):
    s1 = Mock()

    @dm.factory
    def foo():
        return s1()

    f = foo.build(name="not_foo")

    s1.assert_called_once()
    f.set_name.assert_called_with("not_foo")


def test_positional_only_args_error(dm: DeviceManager):
    s1 = Mock()

    with pytest.raises(ValueError, match="positional only argument 'bar'"):

        @dm.factory
        def foo(bar, /):
            return s1()


def test_variadic_args_error(dm: DeviceManager):
    s1 = Mock()
    with pytest.raises(ValueError, match="variadic argument 'args'"):

        @dm.factory
        def foo(*args):
            return s1(*args)


def test_kwargs_factory(dm: DeviceManager):
    s1 = Mock()

    # Factories can have kwargs but they're ignored by the device manager
    @dm.factory
    def foo(**kwargs):
        return s1(**kwargs)

    dm.build_all(s1)
    s1.assert_called_once_with()


def test_devices_or_raise(dm: DeviceManager):
    s1 = Mock(side_effect=RuntimeError("Build failed"))

    @dm.factory
    def foo():
        return s1()

    devices = dm.build_all()
    with RaisesGroup(RaisesExc(RuntimeError, match="Build failed")):
        devices.or_raise()


def test_connect(dm: DeviceManager):
    s1 = Mock(return_value=Mock(spec=OphydV2Device))

    @dm.factory
    def foo():
        return s1()

    con = dm.build_devices(foo).connect()
    s1.assert_called_once()
    s1().connect.assert_called_once_with(timeout=DEFAULT_TIMEOUT, mock=False)

    assert con.devices == {"foo": s1()}
    assert con.build_errors == {}
    assert con.connection_errors == {}


def test_build_and_connect(dm: DeviceManager):
    s1 = Mock(return_value=Mock(spec=OphydV2Device))

    @dm.factory
    def foo():
        return s1()

    con = dm.build_and_connect()
    s1.assert_called_once()
    s1().connect.assert_called_once_with(timeout=DEFAULT_TIMEOUT, mock=False)

    assert con.devices == {"foo": s1()}
    assert con.build_errors == {}
    assert con.connection_errors == {}


def test_factory_options(dm: DeviceManager):
    s1 = Mock(return_value=Mock(spec=OphydV2Device))

    @dm.factory(mock=True, timeout=12)
    def foo():
        return s1()

    con = dm.build_devices(foo).connect()
    s1().connect.assert_called_once_with(mock=True, timeout=12)
    assert con.connection_errors == {}
    assert con.build_errors == {}


def test_connect_failures(dm: DeviceManager):
    s1 = Mock(return_value=Mock(spec=OphydV2Device))
    err = ValueError("Not connected")
    s1.return_value.connect.side_effect = err

    @dm.factory
    def foo():
        return s1()

    con = dm.build_devices(foo).connect()
    s1().connect.assert_called_once_with(mock=False, timeout=DEFAULT_TIMEOUT)
    assert con.connection_errors == {"foo": err}
    assert con.build_errors == {}


def test_connect_or_raise_without_errors(dm: DeviceManager):
    s1 = Mock(return_value=Mock(spec=OphydV2Device))

    @dm.factory
    def foo():
        return s1()

    con = dm.build_devices(foo).connect().or_raise()
    s1.assert_called_once()
    s1().connect.assert_called_once_with(timeout=DEFAULT_TIMEOUT, mock=False)

    assert con == {"foo": s1()}


def test_connect_or_raise_with_build_errors(dm: DeviceManager):
    Mock(return_value=Mock(spec=OphydV2Device))

    @dm.factory
    def foo():
        raise ValueError("foo error")

    with RaisesGroup(RaisesExc(ValueError, match="foo error")):
        dm.build_devices(foo).connect().or_raise()


def test_connect_or_raise_with_connect_errors(dm: DeviceManager):
    s1 = Mock(return_value=Mock(spec=OphydV2Device))
    s1.return_value.connect.side_effect = ValueError("foo connection")

    @dm.factory
    def foo():
        return s1()

    with RaisesGroup(RaisesExc(ValueError, match="foo connection")):
        dm.build_devices(foo).connect().or_raise()


def test_build_and_connect_immediately(dm: DeviceManager):
    s1 = Mock(return_value=Mock(spec=OphydV2Device))

    @dm.factory
    def foo():
        return s1()

    f = foo.build(connect_immediately=True)  # type: ignore
    s1.assert_called_once()
    s1().connect.assert_called_with(mock=False, timeout=DEFAULT_TIMEOUT)
    assert f is s1()


def test_skip_factory(dm: DeviceManager):
    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo():
        return s1()

    @dm.factory(skip=True)
    def bar():
        return s2()

    devices = dm.build_all()
    s1.assert_called_once()
    s2.assert_not_called()
    assert devices.devices == {"foo": s1()}


def test_skip_is_ignored_if_device_is_required(dm: DeviceManager):
    s1 = Mock()
    s2 = Mock()

    @dm.factory
    def foo(bar):
        return s1(bar)

    @dm.factory(skip=True)
    def bar():
        return s2()

    devices = dm.build_all()
    s2.assert_called_once()
    s1.assert_called_once_with(s2())
    assert devices.devices == {"foo": s1(), "bar": s2()}


def test_mock_all(dm: DeviceManager):
    s1 = Mock(return_value=Mock(spec=OphydV2Device))

    @dm.factory
    def foo():
        return s1()

    dm.build_all(mock=True).connect(timeout=11)
    s1().connect.assert_called_once_with(mock=True, timeout=11)


def test_v1_device_factory(dm: DeviceManager):
    s1 = Mock(spec=OphydV1Device)
    s1.__name__ = "S1"

    @dm.v1_init(s1, prefix="S1_PREFIX")  # type: ignore
    def foo(_):
        pass

    with patch("dodal.device_manager.wait_for_connection") as wfc:
        devices = dm.build_all()

    s1.assert_called_once_with(name="foo", prefix="S1_PREFIX")
    device = s1(name="foo", prefix="S1_PREFIX")
    assert devices.devices["foo"] is device
    wfc.assert_called_once_with(device, timeout=DEFAULT_TIMEOUT)


def test_v1_v2_name_clash(dm: DeviceManager):
    s1 = Mock()
    s2 = MagicMock()

    @dm.factory
    def foo():  # type: ignore foo is overridden below
        return s1()

    with pytest.raises(ValueError, match="name"):

        @dm.v1_init(s2, prefix="S2_PREFIX")  # type:ignore
        def foo(_):
            pass


def test_v1_decorator_is_transparent(dm: DeviceManager):
    s1 = MagicMock()

    @dm.v1_init(s1, prefix="S1_PREFIX")  # type: ignore
    def foo(s):
        # arbitrary setup method
        s.special_init_method()

    dev = Mock()
    foo(dev)

    dev.special_init_method.assert_called_once()
    s1.assert_not_called()


def test_v1_no_wait(dm: DeviceManager):
    s1 = Mock()

    @dm.v1_init(s1, prefix="S1_PREFIX", wait=False)  # type: ignore
    def foo(_):
        pass

    with patch("dodal.device_manager.wait_for_connection") as wfc:
        foo.build()
    wfc.assert_not_called()


def test_connect_ignores_v1():
    v1 = Mock(spec=OphydV1Device)
    dbr = DeviceBuildResult({"foo": v1}, {}, {})
    con = dbr.connect()
    # mock raises exception if connect is called
    assert con.devices == {"foo": v1}


def test_v1_mocking(dm: DeviceManager):
    s1 = Mock(return_value=Mock(spec=OphydV1Device))

    @dm.v1_init(s1, prefix="S1_PREFIX", mock=True)  # type: ignore
    def foo(_):
        pass

    with patch("dodal.device_manager.make_fake_device") as mfd:
        dm.build_all()
        mfd.assert_called_once_with(s1)


def test_v1_init_params(dm: DeviceManager):
    # values are passed from fixtures
    s1 = Mock(return_value=Mock(spec=OphydV1Device))
    s1.return_value.mock_add_spec(["set_up_with"])

    @dm.fixture
    def one():
        return "one"

    @dm.v1_init(s1, prefix="S1_PREFIX", wait=False)  # type: ignore
    def foo(s, one, two):
        s.set_up_with(one, two)

    dm.build_devices(foo, fixtures={"two": 2})
    s1.assert_called_once_with(name="foo", prefix="S1_PREFIX")
    s1().set_up_with.assert_called_once_with("one", 2)


def test_lazy_fixtures_non_lazy():
    lf = LazyFixtures(provided={"foo": "bar"}, factories={})
    assert lf["foo"] == "bar"


def test_lazy_fixtures_lazy():
    buzz = Mock(return_value="buzz")
    lf = LazyFixtures(provided={}, factories={"fizz": buzz})

    assert lf.get("foo") is None
    buzz.assert_not_called()

    assert lf.get("fizz") == "buzz"
    buzz.assert_called_once()


def test_lazy_fixtures_provided_overrides_factory():
    buzz = Mock(return_value="buzz")

    lf = LazyFixtures(provided={"fizz": "foo"}, factories={"fizz": buzz})

    assert lf["fizz"] == "foo"
    buzz.assert_not_called()


def test_lazy_fixtures_deduplicated():
    buzz = Mock(return_value="buzz")

    lf = LazyFixtures(provided={"fizz": "foo"}, factories={"fizz": buzz})

    assert len(lf) == 1


def test_lazy_fixtures_iter():
    buzz = Mock(return_value="buzz")

    lf = LazyFixtures(
        provided={"foo": "bar", "one": "two"}, factories={"fizz": buzz, "one": "two"}
    )

    assert sorted(lf) == ["fizz", "foo", "one"]


def test_lazy_fixtures_contains():
    buzz = Mock(return_value="buzz")

    lf = LazyFixtures(
        provided={"foo": "bar", "one": "two"}, factories={"fizz": buzz, "one": "two"}
    )

    assert "foo" in lf
    assert "fizz" in lf
    assert "two" not in lf


def test_docstrings_are_kept(dm: DeviceManager):
    @dm.factory
    def foo():
        """This is the docstring for foo"""
        return Mock()

    @dm.v1_init(Mock(), prefix="MOCK_PREFIX")  # type: ignore
    def bar(_):
        """This is the docstring for bar"""
        pass

    assert foo.__doc__ == "This is the docstring for foo"
    assert bar.__doc__ == "This is the docstring for bar"
