from collections import defaultdict
from unittest.mock import ANY

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
    Apple2Phases,
    PhaseAxisPv,
    UndlatorPhaseAxes,
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


@pytest.fixture
async def mock_phaseAxes(prefix: str = "BLXX-EA-DET-007:") -> UndlatorPhaseAxes:
    async with DeviceCollector(mock=True):
        mock_phaseAxes = UndlatorPhaseAxes(
            prefix="SR10I-MO-",
            top_outer=PhaseAxisPv(set_pv="SERVC-21", axis_pv="RPQ1"),
            top_inner=PhaseAxisPv(set_pv="SERVC-21", axis_pv="RPQ2"),
            btm_outer=PhaseAxisPv(set_pv="SERVC-21", axis_pv="RPQ3"),
            btm_inner=PhaseAxisPv(set_pv="SERVC-21", axis_pv="RPQ4"),
        )
    assert mock_phaseAxes.name == "mock_phaseAxes"
    set_mock_value(mock_phaseAxes.gate, UndulatorGatestatus.close)
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
    return mock_phaseAxes


async def test_in_motion_error(
    mock_id_gap: UndulatorGap, mock_phaseAxes: UndlatorPhaseAxes, RE: RunEngine
):
    set_mock_value(mock_id_gap.gate, UndulatorGatestatus.open)
    with pytest.raises(RuntimeError):
        await mock_id_gap.set("2")
    set_mock_value(mock_phaseAxes.gate, UndulatorGatestatus.open)
    setValue = Apple2Phases("3", "2", "5", "7")
    with pytest.raises(RuntimeError):
        await mock_phaseAxes.set(setValue)


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

    assert await mock_id_gap._cal_timeout() == pytest.approx(expected_timeout, rel=0.1)


async def test_gap_time_out_error(mock_id_gap: UndulatorGap, RE: RunEngine):
    callback_on_mock_put(
        mock_id_gap.user_setpoint,
        lambda *_, **__: set_mock_value(mock_id_gap.gate, UndulatorGatestatus.open),
    )
    set_mock_value(mock_id_gap.velocity, 1000)
    with pytest.raises(TimeoutError):
        await mock_id_gap.set("2")


# async def test_gap_success_set(mock_id_gap: UndulatorGap, RE: RunEngine):
#     expected_value = 20.0
#     callback_on_mock_put(
#         mock_id_gap.user_setpoint,
#         lambda *_, **__: set_mock_value(mock_id_gap.gate, UndulatorGatestatus.open),
#     )

#     def set_complete_move():
#         set_mock_value(mock_id_gap.user_readback, expected_value)
#         set_mock_value(mock_id_gap.gate, UndulatorGatestatus.close)

#     callback_on_mock_put(mock_id_gap.set_move, lambda *_, **__: set_complete_move())
#     RE(bps.abs_set(mock_id_gap, expected_value))
#     get_mock_put(mock_id_gap.set_move).assert_called_once_with(
#         1, wait=True, timeout=10.0
#     )
#     get_mock_put(mock_id_gap.user_setpoint).assert_called_once_with(
#         str(expected_value), wait=True, timeout=10.0
#     )
#     assert await mock_id_gap.user_readback.get_value() == expected_value


async def test_gap_success_scan(mock_id_gap: UndulatorGap, RE: RunEngine):
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


async def test_phase_time_out_error(mock_phaseAxes: UndlatorPhaseAxes, RE: RunEngine):
    setValue = Apple2Phases("3", "2", "5", "7")

    callback_on_mock_put(
        mock_phaseAxes.top_outer.user_setpoint,
        lambda *_, **__: set_mock_value(mock_phaseAxes.gate, UndulatorGatestatus.open),
    )
    set_mock_value(mock_phaseAxes.top_inner.velocity, 1000)
    with pytest.raises(TimeoutError):
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
    mock_phaseAxes: UndlatorPhaseAxes,
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

    assert await mock_phaseAxes._cal_timeout() == pytest.approx(
        expected_timeout, rel=0.1
    )


async def test_phase_success_set(mock_phaseAxes: UndlatorPhaseAxes, RE: RunEngine):
    set_value = Apple2Phases("3", "2", "5", "7")
    expected_value = [3, 2, 5, 7]
    callback_on_mock_put(
        mock_phaseAxes.top_inner.user_setpoint,
        lambda *_, **__: set_mock_value(mock_phaseAxes.gate, UndulatorGatestatus.open),
    )

    def set_complete_move():
        set_mock_value(
            mock_phaseAxes.top_inner.user_setpoint_readback, expected_value[0]
        )
        set_mock_value(
            mock_phaseAxes.top_outer.user_setpoint_readback, expected_value[1]
        )
        set_mock_value(
            mock_phaseAxes.btm_inner.user_setpoint_readback, expected_value[2]
        )
        set_mock_value(
            mock_phaseAxes.btm_outer.user_setpoint_readback, expected_value[3]
        )
        set_mock_value(mock_phaseAxes.gate, UndulatorGatestatus.close)

    callback_on_mock_put(mock_phaseAxes.set_move, lambda *_, **__: set_complete_move())
    RE(bps.abs_set(mock_phaseAxes, set_value))
    get_mock_put(mock_phaseAxes.set_move).assert_called_once_with(
        1, wait=True, timeout=10.0
    )
    get_mock_put(mock_phaseAxes.top_inner.user_setpoint).assert_called_once_with(
        set_value.top_inner, wait=True, timeout=10.0
    )
    get_mock_put(mock_phaseAxes.top_outer.user_setpoint).assert_called_once_with(
        set_value.top_outer, wait=True, timeout=10.0
    )
    get_mock_put(mock_phaseAxes.btm_inner.user_setpoint).assert_called_once_with(
        set_value.btm_inner, wait=True, timeout=10.0
    )
    get_mock_put(mock_phaseAxes.btm_outer.user_setpoint).assert_called_once_with(
        set_value.btm_outer, wait=True, timeout=10.0
    )

    assert await mock_phaseAxes.read() == {
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
        "mock_phaseAxes-btm_outer-user_setpoint_readback": {
            "value": 7,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "mock_phaseAxes-btm_inner-user_setpoint_readback": {
            "value": 5,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
    }
