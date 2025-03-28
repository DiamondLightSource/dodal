from unittest.mock import ANY

import pytest
from bluesky.run_engine import RunEngine
from bluesky.utils import Msg
from ophyd_async.core import (
    init_devices,
)
from ophyd_async.sim import SimMotor

from dodal.plan_stubs.wrapped import (
    move,
    move_relative,
    set_absolute,
    set_relative,
    sleep,
    wait,
)


@pytest.fixture
def x_axis(RE: RunEngine) -> SimMotor:
    with init_devices():
        x_axis = SimMotor()
    return x_axis


@pytest.fixture
def y_axis(RE: RunEngine) -> SimMotor:
    with init_devices():
        y_axis = SimMotor()
    return y_axis


def test_set_absolute(x_axis: SimMotor):
    assert list(set_absolute(x_axis, 0.5)) == [Msg("set", x_axis, 0.5, group=None)]


def test_set_absolute_with_group(x_axis: SimMotor):
    assert list(set_absolute(x_axis, 0.5, group="foo")) == [
        Msg("set", x_axis, 0.5, group="foo")
    ]


def test_set_absolute_with_wait(x_axis: SimMotor):
    msgs = list(set_absolute(x_axis, 0.5, wait=True))
    assert len(msgs) == 2
    assert msgs[0] == Msg("set", x_axis, 0.5, group=ANY)
    assert msgs[1] == Msg("wait", group=msgs[0].kwargs["group"])


def test_set_absolute_with_group_and_wait(x_axis: SimMotor):
    assert list(set_absolute(x_axis, 0.5, group="foo", wait=True)) == [
        Msg("set", x_axis, 0.5, group="foo"),
        Msg("wait", group="foo"),
    ]


def test_set_relative(x_axis: SimMotor):
    assert list(set_relative(x_axis, 0.5)) == [
        Msg("locate", x_axis),
        Msg("set", x_axis, 0.5, group=None),
    ]


def test_set_relative_with_group(x_axis: SimMotor):
    assert list(set_relative(x_axis, 0.5, group="foo")) == [
        Msg("locate", x_axis),
        Msg("set", x_axis, 0.5, group="foo"),
    ]


def test_set_relative_with_wait(x_axis: SimMotor):
    msgs = list(set_relative(x_axis, 0.5, wait=True))
    assert len(msgs) == 3
    assert msgs[0] == Msg("locate", x_axis)
    assert msgs[1] == Msg("set", x_axis, 0.5, group=ANY)
    assert msgs[2] == Msg("wait", group=msgs[1].kwargs["group"])


def test_set_relative_with_group_and_wait(x_axis: SimMotor):
    assert list(set_relative(x_axis, 0.5, group="foo", wait=True)) == [
        Msg("locate", x_axis),
        Msg("set", x_axis, 0.5, group="foo"),
        Msg("wait", group="foo"),
    ]


def test_move(x_axis: SimMotor, y_axis: SimMotor):
    msgs = list(move({x_axis: 0.5, y_axis: 1.0}))
    assert msgs[0] == Msg("set", x_axis, 0.5, group=ANY)
    assert msgs[1] == Msg("set", y_axis, 1.0, group=msgs[0].kwargs["group"])
    assert msgs[2] == Msg("wait", group=msgs[0].kwargs["group"])


def test_move_group(x_axis: SimMotor, y_axis: SimMotor):
    msgs = list(move({x_axis: 0.5, y_axis: 1.0}, group="foo"))
    assert msgs[0] == Msg("set", x_axis, 0.5, group="foo")
    assert msgs[1] == Msg("set", y_axis, 1.0, group="foo")
    assert msgs[2] == Msg("wait", group="foo")


def test_move_relative(x_axis: SimMotor, y_axis: SimMotor):
    msgs = list(move_relative({x_axis: 0.5, y_axis: 1.0}))
    assert msgs[0] == Msg("locate", x_axis)
    assert msgs[1] == Msg("set", x_axis, 0.5, group=ANY)
    group = msgs[1].kwargs["group"]
    assert msgs[2] == Msg("locate", y_axis)
    assert msgs[3] == Msg("set", y_axis, 1.0, group=group)
    assert msgs[4] == Msg("wait", group=group)


def test_move_relative_group(x_axis: SimMotor, y_axis: SimMotor):
    msgs = list(move_relative({x_axis: 0.5, y_axis: 1.0}, group="foo"))
    assert msgs[0] == Msg("locate", x_axis)
    assert msgs[1] == Msg("set", x_axis, 0.5, group="foo")
    assert msgs[2] == Msg("locate", y_axis)
    assert msgs[3] == Msg("set", y_axis, 1.0, group="foo")
    assert msgs[4] == Msg("wait", group="foo")


def test_sleep():
    assert list(sleep(1.5)) == [Msg("sleep", None, 1.5)]


def test_wait():
    # Waits for all groups
    assert list(wait()) == [
        Msg("wait", group=None, timeout=None, error_on_timeout=True)
    ]


def test_wait_group():
    assert list(wait("foo")) == [
        Msg("wait", group="foo", timeout=None, error_on_timeout=True)
    ]


def test_wait_timeout():
    assert list(wait(timeout=5.0)) == [
        Msg("wait", group=None, timeout=5.0, error_on_timeout=True)
    ]


def test_wait_group_and_timeout():
    assert list(wait("foo", 5.0)) == [
        Msg("wait", group="foo", timeout=5.0, error_on_timeout=True)
    ]
