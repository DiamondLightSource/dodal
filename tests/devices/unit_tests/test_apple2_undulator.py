from collections import defaultdict
from typing import Literal

import bluesky.plan_stubs as bps
import pytest
from bluesky.plans import scan
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    DeviceCollector,
    assert_emitted,
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.apple2_undulator import (
    UndulatorGap,
    UndulatorGatestatus,
)


@pytest.fixture
async def mock_id_gap(prefix: str = "BLXX-EA-DET-007:") -> UndulatorGap:
    async with DeviceCollector(mock=True):
        mock_id_gap = UndulatorGap(prefix, "mock_id_gap")
    assert mock_id_gap.name == "mock_id_gap"
    set_mock_value(mock_id_gap.gate, UndulatorGatestatus.close)
    set_mock_value(mock_id_gap.velocity, 1)
    set_mock_value(mock_id_gap.user_readback, 1)
    set_mock_value(mock_id_gap.user_setpoint, "1")
    return mock_id_gap


async def test_in_motion_error(mock_id_gap: UndulatorGap, RE: RunEngine):
    set_mock_value(mock_id_gap.gate, UndulatorGatestatus.open)
    with pytest.raises(RuntimeError):
        await mock_id_gap.set("2")


@pytest.mark.parametrize(
    "velocity, readback,target, expected_timeout",
    [
        (0.7, 20.1, 5.2, 42.5),
        (0.2, 2, 8, 60.0),
        (-0.2, 2, 8, 60.0),
    ],
)
async def test_cal_timout(
    mock_id_gap: UndulatorGap,
    velocity: float,
    readback: float | Literal[2],
    target: float | Literal[8],
    expected_timeout: float,
):
    set_mock_value(mock_id_gap.velocity, velocity)
    set_mock_value(mock_id_gap.user_readback, readback)
    set_mock_value(mock_id_gap.user_setpoint, str(target))

    assert await mock_id_gap._cal_timeout() == pytest.approx(expected_timeout, rel=0.1)


async def test_time_out_error(mock_id_gap: UndulatorGap, RE: RunEngine):
    callback_on_mock_put(
        mock_id_gap.user_setpoint,
        lambda *_, **__: set_mock_value(mock_id_gap.gate, UndulatorGatestatus.open),
    )


async def test_success_set(mock_id_gap: UndulatorGap, RE: RunEngine):
    expected_value = 20.0
    callback_on_mock_put(
        mock_id_gap.user_setpoint,
        lambda *_, **__: set_mock_value(mock_id_gap.gate, UndulatorGatestatus.open),
    )

    def set_complete_move():
        set_mock_value(mock_id_gap.user_readback, expected_value)
        set_mock_value(mock_id_gap.gate, UndulatorGatestatus.close)

    callback_on_mock_put(mock_id_gap.set_move, lambda *_, **__: set_complete_move())
    RE(bps.abs_set(mock_id_gap, expected_value))
    get_mock_put(mock_id_gap.set_move).assert_called_once_with(
        1, wait=True, timeout=10.0
    )
    get_mock_put(mock_id_gap.user_setpoint).assert_called_once_with(
        str(expected_value), wait=True, timeout=10.0
    )
    assert await mock_id_gap.user_readback.get_value() == expected_value


async def test_success_scan(mock_id_gap: UndulatorGap, RE: RunEngine):
    callback_on_mock_put(
        mock_id_gap.user_setpoint,
        lambda *_, **__: set_mock_value(mock_id_gap.gate, UndulatorGatestatus.open),
    )
    output = range(0, 11, 1)

    def new_pos():
        yield from output

    pos = new_pos()

    def set_complete_move():
        set_mock_value(mock_id_gap.user_readback, next(pos))
        set_mock_value(mock_id_gap.gate, UndulatorGatestatus.close)

    callback_on_mock_put(mock_id_gap.set_move, lambda *_, **__: set_complete_move())
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(scan([mock_id_gap], mock_id_gap, 0, 10, 11), capture_emitted)
    assert_emitted(docs, start=1, descriptor=1, event=11, stop=1)
    for i in output:
        assert docs["event"][i]["data"]["mock_id_gap-user_readback"] == i
