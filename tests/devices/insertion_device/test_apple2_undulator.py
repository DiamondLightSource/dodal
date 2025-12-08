from collections.abc import Mapping
from unittest.mock import AsyncMock

import bluesky.plan_stubs as bps
import pytest
from bluesky.plans import scan
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    callback_on_mock_put,
    get_mock_put,
    init_devices,
    set_mock_value,
)
from ophyd_async.testing import (
    assert_emitted,
    assert_reading,
    partial_reading,
)

from dodal.devices.insertion_device.apple2_undulator import (
    DEFAULT_MOTOR_MIN_TIMEOUT,
    Apple2,
    Apple2Controller,
    Apple2LockedPhasesVal,
    Apple2PhasesVal,
    Apple2Val,
    EnabledDisabledUpper,
    EnergyMotorConvertor,
    Pol,
    UndulatorGap,
    UndulatorGateStatus,
    UndulatorJawPhase,
    UndulatorLockedPhaseAxes,
    UndulatorPhaseAxes,
)

# add mock_config_client, mock_id_gap, mock_phase and mock_jaw_phase_axes to pytest.
pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]


@pytest.fixture
async def mock_locked_phase_axes(
    prefix: str = "BLXX-EA-DET-007:",
) -> UndulatorLockedPhaseAxes:
    async with init_devices(mock=True):
        mock_phase_axes = UndulatorLockedPhaseAxes(
            prefix=prefix,
            top_outer="RPQ1",
            btm_inner="RPQ4",
        )
    assert mock_phase_axes.name == "mock_phase_axes"
    set_mock_value(mock_phase_axes.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_phase_axes.top_outer.velocity, 2)
    set_mock_value(mock_phase_axes.btm_inner.velocity, 2)
    set_mock_value(mock_phase_axes.top_outer.user_readback, 2)
    set_mock_value(mock_phase_axes.btm_inner.user_readback, 2)
    set_mock_value(mock_phase_axes.top_outer.user_setpoint_readback, 2)
    set_mock_value(mock_phase_axes.btm_inner.user_setpoint_readback, 2)
    set_mock_value(mock_phase_axes.status, EnabledDisabledUpper.ENABLED)
    return mock_phase_axes


async def test_in_motion_error(
    mock_id_gap: UndulatorGap,
    mock_phase_axes: UndulatorPhaseAxes,
    mock_jaw_phase: UndulatorJawPhase,
):
    set_mock_value(mock_id_gap.gate, UndulatorGateStatus.OPEN)
    with pytest.raises(RuntimeError):
        await mock_id_gap.set(2)
    set_mock_value(mock_phase_axes.gate, UndulatorGateStatus.OPEN)
    set_value = Apple2PhasesVal("3", "2", "5", "7")
    with pytest.raises(RuntimeError):
        await mock_phase_axes.set(set_value)
    set_mock_value(mock_jaw_phase.gate, UndulatorGateStatus.OPEN)
    with pytest.raises(RuntimeError):
        await mock_jaw_phase.set(2)


@pytest.mark.parametrize(
    "velocity, readback,target, expected_timeout",
    [
        (0.7, 20.1, 5.2, 42.5 + DEFAULT_MOTOR_MIN_TIMEOUT),
        (0.2, 2, 8, 60.0 + DEFAULT_MOTOR_MIN_TIMEOUT),
        (-0.2, 2, 8, 60.0 + DEFAULT_MOTOR_MIN_TIMEOUT),
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
    mock_id_gap: UndulatorGap,
):
    callback_on_mock_put(
        mock_id_gap.user_setpoint,
        lambda *_, **__: set_mock_value(mock_id_gap.gate, UndulatorGateStatus.OPEN),
    )
    mock_id_gap.get_timeout = AsyncMock(return_value=0.002)

    with pytest.raises(TimeoutError):
        await mock_id_gap.set(2)


async def test_gap_status_error(mock_id_gap: UndulatorGap):
    set_mock_value(mock_id_gap.status, EnabledDisabledUpper.DISABLED)
    with pytest.raises(RuntimeError):
        await mock_id_gap.set(2)


async def test_gap_success_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    mock_id_gap: UndulatorGap,
):
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

    run_engine(scan([mock_id_gap], mock_id_gap, 0, 10, 11))
    assert_emitted(run_engine_documents, start=1, descriptor=1, event=11, stop=1)
    for i in output:
        assert (
            run_engine_documents["event"][i]["data"]["mock_id_gap-user_readback"] == i
        )


async def test_given_gate_never_closes_then_setting_phases_times_out(
    mock_phase_axes: UndulatorPhaseAxes,
):
    set_value = Apple2PhasesVal("3", "2", "5", "7")

    callback_on_mock_put(
        mock_phase_axes.top_outer.user_setpoint,
        lambda *_, **__: set_mock_value(mock_phase_axes.gate, UndulatorGateStatus.OPEN),
    )
    mock_phase_axes.get_timeout = AsyncMock(return_value=0.002)
    with pytest.raises(TimeoutError):
        await mock_phase_axes.set(set_value)


async def test_phase_status_error(mock_phase_axes: UndulatorPhaseAxes):
    set_value = Apple2PhasesVal("3", "2", "5", "7")
    set_mock_value(mock_phase_axes.status, EnabledDisabledUpper.DISABLED)
    with pytest.raises(RuntimeError):
        await mock_phase_axes.set(set_value)


@pytest.mark.parametrize(
    "velocity, readback,target, expected_timeout",
    [
        (
            [-1, 2, 3, 4],
            [5, 2, 3, 4],
            [-2, 2, 3, 4],
            (14.0 + DEFAULT_MOTOR_MIN_TIMEOUT) * 2,
        ),
        (
            [-1, 0.8, 3, 4],
            [5, -8.5, 3, 4],
            [-2, 0, 3, 4],
            (21.2 + DEFAULT_MOTOR_MIN_TIMEOUT) * 2.0,
        ),
        (
            [-1, 0.8, 0.6, 4],
            [5, -8.5, 2, 4],
            [-2, 0, -5.5, 4],
            (25.0 + DEFAULT_MOTOR_MIN_TIMEOUT) * 2,
        ),
        (
            [-1, 0.8, 0.6, 2.7],
            [5, -8.5, 2, 30],
            [-2, 0, -5.5, -8.8],
            (28.74 + DEFAULT_MOTOR_MIN_TIMEOUT) * 2,
        ),
    ],
)
async def test_phase_cal_timout(
    mock_phase_axes: UndulatorPhaseAxes,
    velocity: list,
    readback: list,
    target: list,
    expected_timeout: float,
):
    set_mock_value(mock_phase_axes.top_inner.velocity, velocity[0])
    set_mock_value(mock_phase_axes.top_outer.velocity, velocity[1])
    set_mock_value(mock_phase_axes.btm_inner.velocity, velocity[2])
    set_mock_value(mock_phase_axes.btm_outer.velocity, velocity[3])

    set_mock_value(mock_phase_axes.top_inner.user_readback, readback[0])
    set_mock_value(mock_phase_axes.top_outer.user_readback, readback[1])
    set_mock_value(mock_phase_axes.btm_inner.user_readback, readback[2])
    set_mock_value(mock_phase_axes.btm_outer.user_readback, readback[3])

    set_mock_value(mock_phase_axes.top_inner.user_setpoint_readback, target[0])
    set_mock_value(mock_phase_axes.top_outer.user_setpoint_readback, target[1])
    set_mock_value(mock_phase_axes.btm_inner.user_setpoint_readback, target[2])
    set_mock_value(mock_phase_axes.btm_outer.user_setpoint_readback, target[3])

    assert await mock_phase_axes.get_timeout() == pytest.approx(
        expected_timeout, rel=0.01
    )


async def test_phase_success_set(
    mock_phase_axes: UndulatorPhaseAxes, run_engine: RunEngine
):
    set_value = Apple2PhasesVal(
        top_inner="3", top_outer="2", btm_inner="5", btm_outer="7"
    )
    callback_on_mock_put(
        mock_phase_axes.top_inner.user_setpoint,
        lambda *_, **__: set_mock_value(mock_phase_axes.gate, UndulatorGateStatus.OPEN),
    )

    def set_complete_move():
        set_mock_value(
            mock_phase_axes.top_inner.user_readback,
            3,
        )
        set_mock_value(
            mock_phase_axes.top_outer.user_readback,
            2,
        )
        set_mock_value(
            mock_phase_axes.btm_inner.user_readback,
            5,
        )
        set_mock_value(
            mock_phase_axes.btm_outer.user_readback,
            7,
        )
        set_mock_value(mock_phase_axes.gate, UndulatorGateStatus.CLOSE)

    callback_on_mock_put(mock_phase_axes.set_move, lambda *_, **__: set_complete_move())
    run_engine(bps.abs_set(mock_phase_axes, set_value, wait=True))
    get_mock_put(mock_phase_axes.set_move).assert_called_once_with(1, wait=True)
    get_mock_put(mock_phase_axes.top_inner.user_setpoint).assert_called_once_with(
        set_value.top_inner, wait=True
    )
    get_mock_put(mock_phase_axes.top_outer.user_setpoint).assert_called_once_with(
        set_value.top_outer, wait=True
    )
    get_mock_put(mock_phase_axes.btm_inner.user_setpoint).assert_called_once_with(
        set_value.btm_inner, wait=True
    )
    get_mock_put(mock_phase_axes.btm_outer.user_setpoint).assert_called_once_with(
        set_value.btm_outer, wait=True
    )

    await assert_reading(
        mock_phase_axes,
        {
            "mock_phase_axes-top_inner-user_readback": partial_reading(3),
            "mock_phase_axes-top_outer-user_readback": partial_reading(2),
            "mock_phase_axes-btm_inner-user_readback": partial_reading(5),
            "mock_phase_axes-btm_outer-user_readback": partial_reading(7),
        },
    )


async def test_given_gate_never_closes_then_setting_jaw_phases_times_out(
    mock_jaw_phase: UndulatorJawPhase,
):
    callback_on_mock_put(
        mock_jaw_phase.jaw_phase.user_setpoint,
        lambda *_, **__: set_mock_value(mock_jaw_phase.gate, UndulatorGateStatus.OPEN),
    )
    mock_jaw_phase.get_timeout = AsyncMock(return_value=0.002)
    with pytest.raises(TimeoutError):
        await mock_jaw_phase.set(2)


async def test_jaw_phase_status_error(mock_jaw_phase: UndulatorJawPhase):
    set_value = 5
    set_mock_value(mock_jaw_phase.status, EnabledDisabledUpper.DISABLED)
    with pytest.raises(RuntimeError):
        await mock_jaw_phase.set(set_value)


@pytest.mark.parametrize(
    "velocity, readback,target, expected_timeout",
    [
        (0.7, 20.1, 5.2, 42.5 + DEFAULT_MOTOR_MIN_TIMEOUT),
        (0.2, 2, 8, 60.0 + DEFAULT_MOTOR_MIN_TIMEOUT),
        (-0.2, 2, 8, 60.0 + DEFAULT_MOTOR_MIN_TIMEOUT),
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
    set_mock_value(mock_jaw_phase.jaw_phase.user_readback, readback)
    set_mock_value(mock_jaw_phase.jaw_phase.user_setpoint_readback, target)

    assert await mock_jaw_phase.get_timeout() == pytest.approx(
        expected_timeout, rel=0.01
    )


async def test_jaw_phase_success_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    mock_jaw_phase: UndulatorJawPhase,
):
    callback_on_mock_put(
        mock_jaw_phase.jaw_phase.user_setpoint,
        lambda *_, **__: set_mock_value(mock_jaw_phase.gate, UndulatorGateStatus.OPEN),
    )
    output = range(0, 11, 1)

    def new_pos():
        yield from output

    pos = new_pos()

    def set_complete_move():
        set_mock_value(mock_jaw_phase.jaw_phase.user_readback, next(pos))
        set_mock_value(mock_jaw_phase.gate, UndulatorGateStatus.CLOSE)

    callback_on_mock_put(mock_jaw_phase.set_move, lambda *_, **__: set_complete_move())

    run_engine(scan([mock_jaw_phase], mock_jaw_phase, 0, 10, 11))
    assert_emitted(run_engine_documents, start=1, descriptor=1, event=11, stop=1)
    for i in output:
        assert (
            run_engine_documents["event"][i]["data"][
                "mock_jaw_phase-jaw_phase-user_readback"
            ]
            == i
        )


@pytest.fixture
async def mock_locked_apple2(
    mock_id_gap: UndulatorGap,
    mock_locked_phase_axes: UndulatorLockedPhaseAxes,
) -> Apple2:
    mock_locked_apple2 = Apple2(
        id_gap=mock_id_gap,
        id_phase=mock_locked_phase_axes,
    )
    return mock_locked_apple2


class DummyLockedApple2Controller(Apple2Controller[Apple2[UndulatorLockedPhaseAxes]]):
    """Dummy class to test core logic of Apple2Controller."""

    def __init__(
        self,
        apple2: Apple2[UndulatorLockedPhaseAxes],
        gap_energy_motor_converter: EnergyMotorConvertor,
        phase_energy_motor_converter: EnergyMotorConvertor,
        name: str = "",
    ) -> None:
        super().__init__(
            apple2=apple2,
            gap_energy_motor_converter=gap_energy_motor_converter,
            phase_energy_motor_converter=phase_energy_motor_converter,
            name=name,
        )

    def _get_apple2_value(self, gap: float, phase: float, pol: Pol) -> Apple2Val:
        return Apple2Val(
            phase=Apple2LockedPhasesVal(
                top_outer=f"{phase:.6f}", btm_inner=f"{phase:.6f}"
            ),
            gap=f"{gap:.6f}",
        )


@pytest.fixture
def configured_gap() -> float:
    return 42.0


@pytest.fixture
def configured_phase() -> float:
    return 7.5


@pytest.fixture
async def mock_locked_controller(
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    configured_gap: float,
    configured_phase: float,
) -> DummyLockedApple2Controller:
    mock_locked_controller = DummyLockedApple2Controller(
        apple2=mock_locked_apple2,
        gap_energy_motor_converter=lambda energy, pol: configured_gap,
        phase_energy_motor_converter=lambda energy, pol: configured_phase,
    )
    return mock_locked_controller


@pytest.mark.parametrize(
    "pol, expect_top_outer, expect_btm_inner",
    [
        (Pol.LH, 0.0, 0.0),
        (Pol.LV, 24.0, 24.0),
        (Pol.PC, 16.5, 16.5),
        (Pol.NC, -15.5, -15.5),
        (Pol.LA, -16.4, 16.4),
        (Pol.LA, 16.4, -16.4),
    ],
)
async def test_id_polarisation_set_for_id_controller(
    mock_locked_controller: DummyLockedApple2Controller,
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    pol: Pol,
    expect_top_outer: float,
    expect_btm_inner: float,
):
    await mock_locked_controller.polarisation.set(pol)
    set_mock_value(mock_locked_apple2.phase().top_outer.user_readback, expect_top_outer)
    set_mock_value(mock_locked_apple2.phase().btm_inner.user_readback, expect_btm_inner)
    assert await mock_locked_controller.polarisation.get_value() == pol


async def test_id_controller_energy_sets_correct_values(
    mock_locked_controller: DummyLockedApple2Controller,
    mock_locked_apple2: Apple2[UndulatorLockedPhaseAxes],
    configured_gap: float,
    configured_phase: float,
):
    mock_locked_apple2.set = AsyncMock()
    mock_locked_controller._check_and_get_pol_setpoint = AsyncMock(return_value=Pol.LH)
    await mock_locked_controller.energy.set(100.0)
    expected_val = Apple2Val(
        phase=Apple2LockedPhasesVal(
            top_outer=f"{configured_phase:.6f}",
            btm_inner=f"{configured_phase:.6f}",
        ),
        gap=f"{configured_gap:.6f}",
    )
    mock_locked_apple2.set.assert_awaited_once_with(id_motor_values=expected_val)
