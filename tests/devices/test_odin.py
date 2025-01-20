# type: ignore # Eiger will soon be ophyd-async https://github.com/DiamondLightSource/dodal/issues/700
from unittest.mock import MagicMock, Mock, patch

import pytest
from ophyd.sim import make_fake_device
from ophyd.status import Status

from dodal.devices.eiger_odin import EigerOdin


def fake_status(in_error: bool):
    status = Status()
    if in_error:
        status.set_exception(Exception)
    else:
        status.set_finished()
    return status


@pytest.fixture
def fake_odin():
    FakeOdin = make_fake_device(EigerOdin)
    fake_odin: EigerOdin = FakeOdin(name="test fake odin")

    return fake_odin


@pytest.mark.parametrize(
    "is_initialised, frames_dropped, frames_timed_out, expected_state",
    [
        (True, False, False, True),
        (False, True, True, False),
        (False, False, False, False),
        (True, True, True, False),
    ],
)
def test_check_and_wait_for_odin_state(
    fake_odin: EigerOdin,
    is_initialised: bool,
    frames_dropped: bool,
    frames_timed_out: bool,
    expected_state: bool,
):
    fake_odin.wait_for_odin_initialised = Mock(return_value=[is_initialised, ""])
    fake_odin.nodes.check_frames_dropped = Mock(return_value=[frames_dropped, ""])
    fake_odin.nodes.check_frames_timed_out = Mock(return_value=[frames_timed_out, ""])

    if is_initialised:
        assert fake_odin.check_and_wait_for_odin_state(None) == expected_state
    else:
        with pytest.raises(RuntimeError):
            fake_odin.check_and_wait_for_odin_state(None)


@pytest.mark.parametrize(
    "fan_connected, fan_on, meta_init, node_error, node_init, expected_error_num, expected_state",
    [
        (True, True, True, False, True, 0, True),
        (False, True, True, False, True, 1, False),
        (False, False, False, True, False, 5, False),
        (True, True, False, False, False, 2, False),
    ],
)
@patch("dodal.devices.eiger_odin.await_value")
def test_wait_for_odin_initialised(
    patch_await,
    fake_odin: EigerOdin,
    fan_connected: bool,
    fan_on: bool,
    meta_init: bool,
    node_error: bool,
    node_init: bool,
    expected_error_num: int,
    expected_state: bool,
):
    def _patch_await(signal, *args, **kwargs):
        signal_and_return = {
            fake_odin.fan.consumers_connected: fake_status(not fan_connected),
            fake_odin.fan.on: fake_status(not fan_on),
            fake_odin.meta.initialised: fake_status(not meta_init),
        }
        return signal_and_return[signal]

    patch_await.side_effect = _patch_await

    fake_odin.nodes.wait_for_no_errors = Mock(
        return_value={fake_status(node_error): "node error" if node_error else ""}
    )
    fake_odin.nodes.get_init_state = Mock(return_value=fake_status(not node_init))

    error_state, error_message = fake_odin.wait_for_odin_initialised(0.5)
    assert error_state == expected_state
    assert (len(error_message) == 0) == expected_state
    assert error_message.count("\n") == (
        0 if expected_state else expected_error_num - 1
    )


@patch("dodal.devices.eiger_odin.await_value")
def test_given_node_in_error_node_error_status_gives_message_and_node_number(
    patch_await,
    fake_odin: EigerOdin,
):
    ERR_MESSAGE = "Help, I'm in error!"
    patch_await.side_effect = lambda *_: fake_status(True)
    fake_odin.nodes.node_0.error_message.sim_put(ERR_MESSAGE)  # type: ignore

    error = fake_odin.nodes.wait_for_no_errors(None)
    error_messages = list(error.values())

    assert any(status.exception for status in error.keys())
    assert any("0" in message for message in error_messages)
    assert any(ERR_MESSAGE in message for message in error_messages)


@pytest.mark.parametrize(
    "meta_writing, OD1_writing, OD2_writing",
    [
        (True, False, False),
        (True, True, True),
        (True, True, False),
    ],
)
def test_wait_for_all_filewriters_to_finish(
    fake_odin: EigerOdin, meta_writing, OD1_writing, OD2_writing
):
    fake_odin.meta.ready.sim_put(meta_writing)  # type: ignore
    fake_odin.nodes.nodes[0].writing.sim_put(OD1_writing)  # type: ignore
    fake_odin.nodes.nodes[1].writing.sim_put(OD2_writing)  # type: ignore
    fake_odin.nodes.nodes[2].writing.sim_put(0)  # type: ignore
    fake_odin.nodes.nodes[3].writing.sim_put(0)  # type: ignore

    status = fake_odin.create_finished_status()

    assert not status.done

    for writer in [
        fake_odin.meta.ready,
        fake_odin.nodes.nodes[0].writing,
        fake_odin.nodes.nodes[1].writing,
    ]:
        writer.sim_put(0)  # type: ignore

    status.wait(1)
    assert status.done
    assert status.success


def test_given_error_on_node_1_when_clear_odin_errors_called_then_resets_all_errors(
    fake_odin: EigerOdin,
):
    nodes = fake_odin.nodes
    nodes.nodes[0].error_message.sim_put("Bad")  # type: ignore
    for node in nodes.nodes:
        node.clear_errors.set = MagicMock()
    nodes.clear_odin_errors()
    for node in nodes.nodes:
        node.clear_errors.set.assert_called_once_with(1)


@patch("dodal.devices.eiger_odin.await_value")
def test_given_await_value_returns_done_status_then_init_state_returns_done(
    patch_await, fake_odin: EigerOdin
):
    patch_await.side_effect = lambda *_: fake_status(False)
    full_status = fake_odin.nodes.get_init_state(None)
    full_status.wait()
    assert full_status.done


def test_given_frames_time_out_then_check_frames_timed_out_returns_error(
    fake_odin: EigerOdin,
):
    fake_odin.nodes.nodes[1].frames_timed_out.sim_put(1)
    error, message = fake_odin.nodes.check_frames_timed_out()
    assert error
    assert "timed out" in message
    assert "1" in message


def test_given_no_frames_time_out_then_check_frames_timed_out_returns_no_error(
    fake_odin: EigerOdin,
):
    error, message = fake_odin.nodes.check_frames_timed_out()
    assert not error
    assert not message


def test_given_frames_dropped_then_check_frames_timed_out_returns_error(
    fake_odin: EigerOdin,
):
    fake_odin.nodes.nodes[2].frames_dropped.sim_put(1)
    error, message = fake_odin.nodes.check_frames_dropped()
    assert error
    assert "dropped" in message
    assert "2" in message


def test_given_no_frames_dropped_then_check_frames_timed_out_returns_no_error(
    fake_odin: EigerOdin,
):
    error, message = fake_odin.nodes.check_frames_timed_out()
    assert not error
    assert not message
    pass
