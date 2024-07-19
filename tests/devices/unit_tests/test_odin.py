from unittest.mock import MagicMock

import pytest
from mockito import when
from ophyd.sim import make_fake_device

from dodal.devices.eiger_odin import EigerOdin


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
def test_check_odin_state(
    fake_odin: EigerOdin,
    is_initialised: bool,
    frames_dropped: bool,
    frames_timed_out: bool,
    expected_state: bool,
):
    when(fake_odin).check_odin_initialised().thenReturn([is_initialised, ""])
    when(fake_odin.nodes).check_frames_dropped().thenReturn([frames_dropped, ""])
    when(fake_odin.nodes).check_frames_timed_out().thenReturn([frames_timed_out, ""])

    if is_initialised:
        assert fake_odin.check_odin_state() == expected_state
    else:
        with pytest.raises(Exception):
            fake_odin.check_odin_state()


@pytest.mark.parametrize(
    "fan_connected, fan_on, meta_init, node_error, node_init, expected_error_num, expected_state",
    [
        (True, True, True, False, True, 0, True),
        (False, True, True, False, True, 1, False),
        (False, False, False, True, False, 5, False),
        (True, True, False, False, False, 2, False),
    ],
)
def test_check_odin_initialised(
    fake_odin: EigerOdin,
    fan_connected: bool,
    fan_on: bool,
    meta_init: bool,
    node_error: bool,
    node_init: bool,
    expected_error_num: int,
    expected_state: bool,
):
    when(fake_odin.fan.consumers_connected).get().thenReturn(fan_connected)
    when(fake_odin.fan.on).get().thenReturn(fan_on)
    when(fake_odin.meta.initialised).get().thenReturn(meta_init)
    when(fake_odin.nodes).get_error_state().thenReturn(
        [node_error, "node error" if node_error else ""]
    )
    when(fake_odin.nodes).get_init_state().thenReturn(node_init)

    error_state, error_message = fake_odin.check_odin_initialised()
    assert error_state == expected_state
    assert (len(error_message) == 0) == expected_state
    assert error_message.count("\n") == (
        0 if expected_state else expected_error_num - 1
    )


def test_given_node_in_error_node_error_status_gives_message_and_node_number(
    fake_odin: EigerOdin,
):
    ERR_MESSAGE = "Help, I'm in error!"
    fake_odin.nodes.node_0.error_status.sim_put(True)  # type: ignore
    fake_odin.nodes.node_0.error_message.sim_put(ERR_MESSAGE)  # type: ignore

    in_error, message = fake_odin.nodes.get_error_state()

    assert in_error
    assert "0" in message
    assert ERR_MESSAGE in message


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
