import asyncio
from collections import defaultdict
from unittest.mock import ANY, AsyncMock

import bluesky.plan_stubs as bps
import pytest
from bluesky.plans import scan
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_emitted,
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.apple2_undulator import (
    Apple2PhasesVal,
    UndulatorGap,
    UndulatorGateStatus,
    UndulatorJawPhase,
    UndulatorPhaseAxes,
)


@pytest.fixture
async def mock_id_gap(prefix: str = "BLXX-EA-DET-007:") -> UndulatorGap:
    async with init_devices(mock=True):
        mock_id_gap = UndulatorGap(prefix, "mock_id_gap")
    assert mock_id_gap.name == "mock_id_gap"
    set_mock_value(mock_id_gap.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_id_gap.velocity, 1)
    set_mock_value(mock_id_gap.user_readback, 1)
    set_mock_value(mock_id_gap.user_setpoint, "1")
    set_mock_value(mock_id_gap.fault, 0)
    return mock_id_gap


@pytest.fixture
async def mock_phaseAxes(prefix: str = "BLXX-EA-DET-007:") -> UndulatorPhaseAxes:
    async with init_devices(mock=True):
        mock_phaseAxes = UndulatorPhaseAxes(
            prefix=prefix,
            top_outer="RPQ1",
            top_inner="RPQ2",
            btm_outer="RPQ3",
            btm_inner="RPQ4",
        )
    assert mock_phaseAxes.name == "mock_phaseAxes"
    set_mock_value(mock_phaseAxes.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_phaseAxes.top_outer.velocity, 2)
    set_mock_value(mock_phaseAxes.top_inner.velocity, 2)
    set_mock_value(mock_phaseAxes.btm_outer.velocity, 2)
    set_mock_value(mock_phaseAxes.btm_inner.velocity, 2)
    set_mock_value(mock_phaseAxes.top_outer.user_setpoint_readback, 2)
    set_mock_value(mock_phaseAxes.top_inner.user_setpoint_readback, 2)
    set_mock_value(mock_phaseAxes.btm_outer.user_setpoint_readback, 2)
    set_mock_value(mock_phaseAxes.btm_inner.user_setpoint_readback, 2)
    set_mock_value(mock_phaseAxes.top_outer.user_setpoint_demand_readback, 2)
    set_mock_value(mock_phaseAxes.top_inner.user_setpoint_demand_readback, 2)
    set_mock_value(mock_phaseAxes.btm_outer.user_setpoint_demand_readback, 2)
    set_mock_value(mock_phaseAxes.btm_inner.user_setpoint_demand_readback, 2)
    set_mock_value(mock_phaseAxes.fault, 0)
    return mock_phaseAxes


@pytest.fixture
async def mock_jaw_phase(prefix: str = "BLXX-EA-DET-007:") -> UndulatorJawPhase:
    async with init_devices(mock=True):
        mock_jaw_phase = UndulatorJawPhase(
            prefix=prefix, move_pv="RPQ1", jaw_phase="JAW"
        )
    set_mock_value(mock_jaw_phase.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_jaw_phase.jaw_phase.velocity, 2)
    set_mock_value(mock_jaw_phase.jaw_phase.user_setpoint_readback, 0)
    set_mock_value(mock_jaw_phase.jaw_phase.user_setpoint_demand_readback, 0)
    set_mock_value(mock_jaw_phase.fault, 0)
    return mock_jaw_phase


async def test_in_motion_error(
    mock_id_gap: UndulatorGap,
    mock_phaseAxes: UndulatorPhaseAxes,
    mock_jaw_phase: UndulatorJawPhase,
):
    set_mock_value(mock_id_gap.gate, UndulatorGateStatus.OPEN)
    with pytest.raises(RuntimeError):
        await mock_id_gap.set(2)
    set_mock_value(mock_phaseAxes.gate, UndulatorGateStatus.OPEN)
    setValue = Apple2PhasesVal("3", "2", "5", "7")
    with pytest.raises(RuntimeError):
        await mock_phaseAxes.set(setValue)
    set_mock_value(mock_jaw_phase.gate, UndulatorGateStatus.OPEN)
    with pytest.raises(RuntimeError):
        await mock_jaw_phase.set(2)


@pytest.mark.parametrize(
    "velocity, readback,target, expected_timeout",
    [
        (0.7, 20.1, 5.2, 42.5),
        (0.2, 2, 8, 60.0),
        (-0.2, 2, 8, 60.0),
    ],
)
async def test_gap_cal_timout(
    mock_id_gap: UndulatorGap,
    velocity: float,
    readback: float,
    target: float,
    expected_timeout: float,
):
    set_mock_value(mock_id_gap.velocity, velocity)
    set_mock_value(mock_id_gap.user_readback, readback)
    set_mock_value(mock_id_gap.user_setpoint, str(target))

    assert await mock_id_gap.get_timeout() == pytest.approx(expected_timeout, rel=0.1)


async def test_given_gate_never_closes_then_setting_gaps_times_out(
    mock_id_gap: UndulatorGap, RE: RunEngine
):
    callback_on_mock_put(
        mock_id_gap.user_setpoint,
        lambda *_, **__: set_mock_value(mock_id_gap.gate, UndulatorGateStatus.OPEN),
    )
    mock_id_gap.get_timeout = AsyncMock(return_value=0.01)
    with pytest.raises(asyncio.TimeoutError):
        await mock_id_gap.set(2)


async def test_gap_status_error(mock_id_gap: UndulatorGap, RE: RunEngine):
    set_mock_value(mock_id_gap.fault, 1.0)
    with pytest.raises(RuntimeError):
        await mock_id_gap.set(2)


async def test_gap_success_scan(mock_id_gap: UndulatorGap, RE: RunEngine):
    callback_on_mock_put(
        mock_id_gap.user_setpoint,
        lambda *_, **__: set_mock_value(mock_id_gap.gate, UndulatorGateStatus.OPEN),
    )
    output = range(0, 11, 1)

    def new_pos():
        yield from output

    pos = new_pos()

    def set_complete_move():
        set_mock_value(mock_id_gap.user_readback, next(pos))
        set_mock_value(mock_id_gap.gate, UndulatorGateStatus.CLOSE)

    callback_on_mock_put(mock_id_gap.set_move, lambda *_, **__: set_complete_move())
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(scan([mock_id_gap], mock_id_gap, 0, 10, 11), capture_emitted)
    assert_emitted(docs, start=1, descriptor=1, event=11, stop=1)
    for i in output:
        assert docs["event"][i]["data"]["mock_id_gap-user_readback"] == i


async def test_given_gate_never_closes_then_setting_phases_times_out(
    mock_phaseAxes: UndulatorPhaseAxes, RE: RunEngine
):
    setValue = Apple2PhasesVal("3", "2", "5", "7")

    callback_on_mock_put(
        mock_phaseAxes.top_outer.user_setpoint,
        lambda *_, **__: set_mock_value(mock_phaseAxes.gate, UndulatorGateStatus.OPEN),
    )
    mock_phaseAxes.get_timeout = AsyncMock(return_value=0.01)

    with pytest.raises(asyncio.TimeoutError):
        await mock_phaseAxes.set(setValue)


async def test_phase_status_error(mock_phaseAxes: UndulatorPhaseAxes, RE: RunEngine):
    setValue = Apple2PhasesVal("3", "2", "5", "7")
    set_mock_value(mock_phaseAxes.fault, 1.0)
    with pytest.raises(RuntimeError):
        await mock_phaseAxes.set(setValue)


@pytest.mark.parametrize(
    "velocity, readback,target, expected_timeout",
    [
        ([-1, 2, 3, 4], [5, 2, 3, 4], [-2, 2, 3, 4], 14.0),
        ([-1, 0.8, 3, 4], [5, -8.5, 3, 4], [-2, 0, 3, 4], 21.2),
        ([-1, 0.8, 0.6, 4], [5, -8.5, 2, 4], [-2, 0, -5.5, 4], 25.0),
        ([-1, 0.8, 0.6, 2.7], [5, -8.5, 2, 30], [-2, 0, -5.5, -8.8], 28.7),
    ],
)
async def test_phase_cal_timout(
    mock_phaseAxes: UndulatorPhaseAxes,
    velocity: list,
    readback: list,
    target: list,
    expected_timeout: float,
):
    set_mock_value(mock_phaseAxes.top_inner.velocity, velocity[0])
    set_mock_value(mock_phaseAxes.top_outer.velocity, velocity[1])
    set_mock_value(mock_phaseAxes.btm_inner.velocity, velocity[2])
    set_mock_value(mock_phaseAxes.btm_outer.velocity, velocity[3])

    set_mock_value(mock_phaseAxes.top_inner.user_setpoint_readback, readback[0])
    set_mock_value(mock_phaseAxes.top_outer.user_setpoint_readback, readback[1])
    set_mock_value(mock_phaseAxes.btm_inner.user_setpoint_readback, readback[2])
    set_mock_value(mock_phaseAxes.btm_outer.user_setpoint_readback, readback[3])

    set_mock_value(mock_phaseAxes.top_inner.user_setpoint_demand_readback, target[0])
    set_mock_value(mock_phaseAxes.top_outer.user_setpoint_demand_readback, target[1])
    set_mock_value(mock_phaseAxes.btm_inner.user_setpoint_demand_readback, target[2])
    set_mock_value(mock_phaseAxes.btm_outer.user_setpoint_demand_readback, target[3])

    assert await mock_phaseAxes.get_timeout() == pytest.approx(
        expected_timeout, rel=0.1
    )


async def test_phase_success_set(mock_phaseAxes: UndulatorPhaseAxes, RE: RunEngine):
    set_value = Apple2PhasesVal(
        top_inner="3", top_outer="2", btm_inner="5", btm_outer="7"
    )
    callback_on_mock_put(
        mock_phaseAxes.top_inner.user_setpoint,
        lambda *_, **__: set_mock_value(mock_phaseAxes.gate, UndulatorGateStatus.OPEN),
    )

    def set_complete_move():
        set_mock_value(
            mock_phaseAxes.top_inner.user_setpoint_readback,
            3,
        )
        set_mock_value(
            mock_phaseAxes.top_outer.user_setpoint_readback,
            2,
        )
        set_mock_value(
            mock_phaseAxes.btm_inner.user_setpoint_readback,
            5,
        )
        set_mock_value(
            mock_phaseAxes.btm_outer.user_setpoint_readback,
            7,
        )
        set_mock_value(mock_phaseAxes.gate, UndulatorGateStatus.CLOSE)

    callback_on_mock_put(mock_phaseAxes.set_move, lambda *_, **__: set_complete_move())
    RE(bps.abs_set(mock_phaseAxes, set_value, wait=True))
    get_mock_put(mock_phaseAxes.set_move).assert_called_once_with(1, wait=True)
    get_mock_put(mock_phaseAxes.top_inner.user_setpoint).assert_called_once_with(
        set_value.top_inner, wait=True
    )
    get_mock_put(mock_phaseAxes.top_outer.user_setpoint).assert_called_once_with(
        set_value.top_outer, wait=True
    )
    get_mock_put(mock_phaseAxes.btm_inner.user_setpoint).assert_called_once_with(
        set_value.btm_inner, wait=True
    )
    get_mock_put(mock_phaseAxes.btm_outer.user_setpoint).assert_called_once_with(
        set_value.btm_outer, wait=True
    )

    expected_in_reading = {
        "mock_phaseAxes-top_inner-user_setpoint_readback": {
            "value": 3,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "mock_phaseAxes-top_outer-user_setpoint_readback": {
            "value": 2,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "mock_phaseAxes-btm_inner-user_setpoint_readback": {
            "value": 5,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "mock_phaseAxes-btm_outer-user_setpoint_readback": {
            "value": 7,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
    }
    actual_reading = await mock_phaseAxes.read()
    assert expected_in_reading.items() <= actual_reading.items()


async def test_given_gate_never_closes_then_setting_jaw_phases_times_out(
    mock_jaw_phase: UndulatorJawPhase,
):
    callback_on_mock_put(
        mock_jaw_phase.jaw_phase.user_setpoint,
        lambda *_, **__: set_mock_value(mock_jaw_phase.gate, UndulatorGateStatus.OPEN),
    )
    mock_jaw_phase.get_timeout = AsyncMock(return_value=0.01)
    with pytest.raises(asyncio.TimeoutError):
        await mock_jaw_phase.set(2)


async def test_jaw_phase_status_error(mock_jaw_phase: UndulatorJawPhase):
    setValue = 5
    set_mock_value(mock_jaw_phase.fault, 1.0)
    with pytest.raises(RuntimeError):
        await mock_jaw_phase.set(setValue)


@pytest.mark.parametrize(
    "velocity, readback,target, expected_timeout",
    [
        (0.7, 20.1, 5.2, 42.5),
        (0.2, 2, 8, 60.0),
        (-0.2, 2, 8, 60.0),
    ],
)
async def test_jaw_phase_cal_timout(
    mock_jaw_phase: UndulatorJawPhase,
    velocity: float,
    readback: float,
    target: float,
    expected_timeout: float,
):
    set_mock_value(mock_jaw_phase.jaw_phase.velocity, velocity)
    set_mock_value(mock_jaw_phase.jaw_phase.user_setpoint_readback, readback)
    set_mock_value(mock_jaw_phase.jaw_phase.user_setpoint_demand_readback, target)

    assert await mock_jaw_phase.get_timeout() == pytest.approx(
        expected_timeout, rel=0.1
    )


async def test_jaw_phase_success_scan(mock_jaw_phase: UndulatorJawPhase, RE: RunEngine):
    callback_on_mock_put(
        mock_jaw_phase.jaw_phase.user_setpoint,
        lambda *_, **__: set_mock_value(mock_jaw_phase.gate, UndulatorGateStatus.OPEN),
    )
    output = range(0, 11, 1)

    def new_pos():
        yield from output

    pos = new_pos()

    def set_complete_move():
        set_mock_value(mock_jaw_phase.jaw_phase.user_setpoint_readback, next(pos))
        set_mock_value(mock_jaw_phase.gate, UndulatorGateStatus.CLOSE)

    callback_on_mock_put(mock_jaw_phase.set_move, lambda *_, **__: set_complete_move())
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(scan([mock_jaw_phase], mock_jaw_phase, 0, 10, 11), capture_emitted)
    assert_emitted(docs, start=1, descriptor=1, event=11, stop=1)
    for i in output:
        assert (
            docs["event"][i]["data"]["mock_jaw_phase-jaw_phase-user_setpoint_readback"]
            == i
        )
