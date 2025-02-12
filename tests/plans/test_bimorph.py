import asyncio
import unittest
import unittest.mock
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import ANY, Mock, call

import bluesky.plan_stubs as bps
import pytest
from bluesky.protocols import Readable
from bluesky.run_engine import RunEngine
from bluesky.utils import Msg
from numpy import linspace
from ophyd_async.core import StandardDetector, init_devices, walk_rw_signals
from ophyd_async.sim import PatternDetector
from ophyd_async.testing import callback_on_mock_put, get_mock_put, set_mock_value

from dodal.devices.bimorph_mirror import BimorphMirror, BimorphMirrorStatus
from dodal.devices.slits import Slits
from dodal.plans.bimorph import (
    BimorphState,
    SlitDimension,
    bimorph_optimisation,
    capture_bimorph_state,
    inner_scan,
    move_slits,
    restore_bimorph_state,
)

VALID_BIMORPH_CHANNELS = [3]


@pytest.fixture(params=VALID_BIMORPH_CHANNELS)
def mirror(request, RE: RunEngine) -> BimorphMirror:
    number_of_channels = request.param

    with init_devices(mock=True):
        bm = BimorphMirror(
            prefix="FAKE-PREFIX:",
            number_of_channels=number_of_channels,
        )

    return bm


@pytest.fixture
def mirror_with_mocked_put(mirror: BimorphMirror) -> BimorphMirror:
    async def busy_idle():
        await asyncio.sleep(0)
        set_mock_value(mirror.status, BimorphMirrorStatus.BUSY)
        await asyncio.sleep(0)
        set_mock_value(mirror.status, BimorphMirrorStatus.IDLE)

    async def status(*_, **__):
        asyncio.create_task(busy_idle())

    for signal in walk_rw_signals(mirror).values():
        callback_on_mock_put(signal, status)

    for channel in mirror.channels.values():

        def vout_propogation_and_status(
            value: float, wait=False, signal=channel.output_voltage
        ):
            signal.set(value, wait=wait)
            asyncio.create_task(busy_idle())

        callback_on_mock_put(channel.target_voltage, vout_propogation_and_status)

    return mirror


@pytest.fixture
def slits(RE: RunEngine) -> Slits:
    """Mock slits with propagation from setpoint to readback."""
    with init_devices(mock=True):
        slits = Slits("FAKE-PREFIX:")

    for motor in [slits.x_gap, slits.y_gap, slits.x_centre, slits.y_centre]:
        # Set velocity to avoid zero velocity error:
        set_mock_value(motor.velocity, 1)

        def callback(value, wait=False, signal=motor.user_readback):
            set_mock_value(signal, value)

        callback_on_mock_put(motor.user_setpoint, callback)
    return slits


@pytest.fixture
async def oav(RE: RunEngine, tmp_path: Path) -> StandardDetector:
    with init_devices(mock=True):
        det = PatternDetector(tmp_path / "foo.temp")
    return det


@pytest.fixture(params=[0, 1])
async def detectors(request, oav: StandardDetector) -> list[Readable]:
    return [oav] * request.param


@pytest.fixture(params=[True, False])
def initial_voltage_list(request, mirror) -> list[float] | None:
    if request.param:
        return [0.0 for _ in range(len(mirror.channels))]
    else:
        return None


@pytest.mark.parametrize("dimension", [SlitDimension.X, SlitDimension.Y])
@pytest.mark.parametrize("gap", [1.0])
@pytest.mark.parametrize("center", [2.0])
async def test_move_slits(
    slits: Slits,
    dimension: SlitDimension,
    gap: float,
    center: float,
):
    messages = list(move_slits(slits, dimension, gap, center))

    if dimension == SlitDimension.X:
        gap_signal = slits.x_gap
        centre_signal = slits.x_centre
    else:
        gap_signal = slits.y_gap
        centre_signal = slits.y_centre

    assert [
        Msg("set", gap_signal, gap, group=ANY),
        Msg("wait", None, group=ANY),
        Msg("set", centre_signal, center, group=ANY),
        Msg("wait", None, group=ANY),
    ] == messages


def test_save_and_restore(RE: RunEngine, mirror: BimorphMirror, slits: Slits):
    signals = [
        slits.x_gap.user_setpoint,
        slits.y_gap.user_setpoint,
        slits.x_centre.user_setpoint,
        slits.y_centre.user_setpoint,
        mirror.channels[1].output_voltage,
    ]
    puts = [get_mock_put(signal) for signal in signals]

    def plan():
        state = yield from capture_bimorph_state(mirror, slits)

        for signal in signals:
            yield from bps.abs_set(signal, 4.0, wait=True)

        yield from restore_bimorph_state(mirror, slits, state)

    RE(plan())

    for put in puts:
        assert put.call_args_list == [call(4.0, wait=True), call(0.0, wait=True)]


@pytest.mark.parametrize("active_dimension", [SlitDimension.X, SlitDimension.Y])
@pytest.mark.parametrize("active_slit_center_start", [0.0])
@pytest.mark.parametrize("active_slit_center_end", [200])
@pytest.mark.parametrize("active_slit_size", [0.05])
@pytest.mark.parametrize("number_of_slit_positions", [3])
@pytest.mark.parametrize(
    "run_metadata", [None, {"outer_uid": "0", "bimorph_position_index": 0}]
)
@unittest.mock.patch("dodal.plans.bimorph.bps.trigger_and_read")
@unittest.mock.patch("dodal.plans.bimorph.move_slits")
class TestInnerScan:
    def test_inner_scan_moves_slits(
        self,
        mock_move_slits: Mock,
        mock_bps_trigger_and_read: Mock,
        detectors: list[Readable],
        RE: RunEngine,
        mirror: BimorphMirror,
        slits: Slits,
        active_dimension: SlitDimension,
        active_slit_center_start: float,
        active_slit_center_end: float,
        active_slit_size: float,
        number_of_slit_positions: int,
        run_metadata: dict[str, Any] | None,
    ):
        RE(
            inner_scan(
                detectors,
                mirror,
                slits,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                number_of_slit_positions,
                run_metadata,
            )
        )

        call_list = [
            call(slits, active_dimension, active_slit_size, value)
            for value in linspace(
                active_slit_center_start,
                active_slit_center_end,
                number_of_slit_positions,
            )
        ]

        assert mock_move_slits.call_args_list == call_list

    def test_inner_scan_triggers_and_reads(
        self,
        mock_move_slits: Mock,
        mock_bps_trigger_and_read: Mock,
        detectors: list[Readable],
        RE: RunEngine,
        mirror: BimorphMirror,
        slits: Slits,
        active_dimension: SlitDimension,
        active_slit_center_start: float,
        active_slit_center_end: float,
        active_slit_size: float,
        number_of_slit_positions: int,
        run_metadata: dict[str, Any] | None,
    ):
        RE(
            inner_scan(
                detectors,
                mirror,
                slits,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                number_of_slit_positions,
                run_metadata,
            )
        )

        call_list = [
            call((*detectors, slits, mirror))
            for _ in linspace(
                active_slit_center_start,
                active_slit_center_end,
                number_of_slit_positions,
            )
        ]
        assert mock_bps_trigger_and_read.call_args_list == call_list

    def test_inner_scan_writes_run_metadata(
        self,
        mock_move_slits: Mock,
        mock_bps_trigger_and_read: Mock,
        detectors: list[Readable],
        RE: RunEngine,
        mirror: BimorphMirror,
        slits: Slits,
        active_dimension: SlitDimension,
        active_slit_center_start: float,
        active_slit_center_end: float,
        active_slit_size: float,
        number_of_slit_positions: int,
        run_metadata: dict[str, Any] | None,
    ):
        start_docs = []

        def get_start(_, doc):
            start_docs.append(doc)

        RE(
            inner_scan(
                detectors,
                mirror,
                slits,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                number_of_slit_positions,
                run_metadata,
            ),
            {"start": [get_start]},
        )

        start_doc = start_docs[0]

        if run_metadata is not None:
            assert (
                start_doc["outer_uid"] == "0"
                and start_doc["bimorph_position_index"] == 0
            )


@pytest.mark.parametrize("voltage_increment", [100.0])
@pytest.mark.parametrize("active_dimension", [SlitDimension.X, SlitDimension.Y])
@pytest.mark.parametrize("active_slit_center_start", [0.0])
@pytest.mark.parametrize("active_slit_center_end", [200.0])
@pytest.mark.parametrize("active_slit_size", [0.05])
@pytest.mark.parametrize("inactive_slit_center", [0.0])
@pytest.mark.parametrize("inactive_slit_size", [0.05])
@pytest.mark.parametrize("number_of_slit_positions", [3])
@pytest.mark.parametrize("bimorph_settle_time", [0.0])
@unittest.mock.patch("dodal.plans.bimorph.bps.sleep")
@unittest.mock.patch("dodal.plans.bimorph.restore_bimorph_state")
@unittest.mock.patch("dodal.plans.bimorph.move_slits")
@unittest.mock.patch("dodal.plans.bimorph.inner_scan")
class TestBimorphOptimisation:
    """Run full bimorph_optimisation plan with mocked devices and plan stubs."""

    @pytest.fixture
    def start_state(self, mirror_with_mocked_put: BimorphMirror) -> BimorphState:
        return BimorphState(
            [10.0 for _ in range(len(mirror_with_mocked_put.channels))],
            0.0,
            0.0,
            0.0,
            0.0,
        )

    @pytest.fixture
    def mock_capture_bimorph_state(
        self, start_state: BimorphState
    ) -> Generator[Mock, None, None]:
        with unittest.mock.patch(
            "dodal.plans.bimorph.capture_bimorph_state"
        ) as mock_obj:

            def mock_capture_plan_stub(
                *args: Any, **kwargs: Any
            ) -> Generator[None, None, BimorphState]:
                # return start_state without yielding Msg to RE:
                yield from iter([])
                return start_state

            mock_obj.side_effect = mock_capture_plan_stub

            yield mock_obj

    async def test_settle_time_called(
        self,
        mock_inner_scan: Mock,
        mock_move_slits: Mock,
        mock_restore_bimorph_state: Mock,
        mock_bps_sleep: Mock,
        mock_capture_bimorph_state: Mock,
        detectors: list[Readable],
        RE: RunEngine,
        mirror_with_mocked_put: BimorphMirror,
        slits: Slits,
        voltage_increment: float,
        active_dimension: SlitDimension,
        active_slit_center_start: float,
        active_slit_center_end: float,
        active_slit_size: float,
        inactive_slit_center: float,
        inactive_slit_size: float,
        number_of_slit_positions: int,
        bimorph_settle_time: float,
        initial_voltage_list: list[float],
    ):
        RE(
            bimorph_optimisation(
                detectors,
                mirror_with_mocked_put,
                slits,
                voltage_increment,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                inactive_slit_center,
                inactive_slit_size,
                number_of_slit_positions,
                bimorph_settle_time,
                initial_voltage_list,
            )
        )
        assert [
            call(bimorph_settle_time)
            for _ in range(len(mirror_with_mocked_put.channels))
        ] == mock_bps_sleep.call_args_list

    async def test_bimorph_state_captured(
        self,
        mock_inner_scan: Mock,
        mock_move_slits: Mock,
        mock_restore_bimorph_state: Mock,
        mock_bps_sleep: Mock,
        mock_capture_bimorph_state: Mock,
        detectors: list[Readable],
        RE: RunEngine,
        mirror_with_mocked_put: BimorphMirror,
        slits: Slits,
        voltage_increment: float,
        active_dimension: SlitDimension,
        active_slit_center_start: float,
        active_slit_center_end: float,
        active_slit_size: float,
        inactive_slit_center: float,
        inactive_slit_size: float,
        number_of_slit_positions: int,
        bimorph_settle_time: float,
        initial_voltage_list: list[float],
        start_state,
    ):
        RE(
            bimorph_optimisation(
                detectors,
                mirror_with_mocked_put,
                slits,
                voltage_increment,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                inactive_slit_center,
                inactive_slit_size,
                number_of_slit_positions,
                bimorph_settle_time,
                initial_voltage_list,
            )
        )

        assert mock_capture_bimorph_state.call_args == call(
            mirror_with_mocked_put, slits
        )

    async def test_plan_sets_mirror_start_position(
        self,
        mock_inner_scan: Mock,
        mock_move_slits: Mock,
        mock_restore_bimorph_state: Mock,
        mock_bps_sleep: Mock,
        mock_capture_bimorph_state: Mock,
        detectors: list[Readable],
        RE: RunEngine,
        mirror_with_mocked_put: BimorphMirror,
        slits: Slits,
        voltage_increment: float,
        active_dimension: SlitDimension,
        active_slit_center_start: float,
        active_slit_center_end: float,
        active_slit_size: float,
        inactive_slit_center: float,
        inactive_slit_size: float,
        number_of_slit_positions: int,
        bimorph_settle_time: float,
        initial_voltage_list: list[float],
        start_state: BimorphState,
    ):
        inactive_dimension = (
            SlitDimension.Y if active_dimension == SlitDimension.X else SlitDimension.X
        )

        RE(
            bimorph_optimisation(
                detectors,
                mirror_with_mocked_put,
                slits,
                voltage_increment,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                inactive_slit_center,
                inactive_slit_size,
                number_of_slit_positions,
                bimorph_settle_time,
                initial_voltage_list,
            )
        )
        assert [
            call(slits, active_dimension, active_slit_size, active_slit_center_start),
            call(slits, inactive_dimension, inactive_slit_size, inactive_slit_center),
        ] == mock_move_slits.call_args_list

    async def test_plan_calls_inner_scan(
        self,
        mock_inner_scan: Mock,
        mock_move_slits: Mock,
        mock_restore_bimorph_state: Mock,
        mock_bps_sleep: Mock,
        mock_capture_bimorph_state: Mock,
        detectors: list[Readable],
        RE: RunEngine,
        mirror_with_mocked_put: BimorphMirror,
        slits: Slits,
        voltage_increment: float,
        active_dimension: SlitDimension,
        active_slit_center_start: float,
        active_slit_center_end: float,
        active_slit_size: float,
        inactive_slit_center: float,
        inactive_slit_size: float,
        number_of_slit_positions: int,
        bimorph_settle_time: float,
        initial_voltage_list: list[float],
        start_state: BimorphState,
    ):
        RE(
            bimorph_optimisation(
                detectors,
                mirror_with_mocked_put,
                slits,
                voltage_increment,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                inactive_slit_center,
                inactive_slit_size,
                number_of_slit_positions,
                bimorph_settle_time,
                initial_voltage_list,
            )
        )
        assert [
            call(
                detectors,
                mirror_with_mocked_put,
                slits,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                number_of_slit_positions,
                run_metadata={"outer_uid": ANY, "bimorph_position_index": i},
            )
            for i in range(len(mirror_with_mocked_put.channels) + 1)
        ] == mock_inner_scan.call_args_list

    async def test_plan_puts_to_bimorph(
        self,
        mock_inner_scan: Mock,
        mock_move_slits: Mock,
        mock_restore_bimorph_state: Mock,
        mock_bps_sleep: Mock,
        mock_capture_bimorph_state: Mock,
        detectors: list[Readable],
        RE: RunEngine,
        mirror_with_mocked_put: BimorphMirror,
        slits: Slits,
        voltage_increment: float,
        active_dimension: SlitDimension,
        active_slit_center_start: float,
        active_slit_center_end: float,
        active_slit_size: float,
        inactive_slit_center: float,
        inactive_slit_size: float,
        number_of_slit_positions: int,
        bimorph_settle_time: float,
        initial_voltage_list: list[float],
        start_state: BimorphState,
    ):
        RE(
            bimorph_optimisation(
                detectors,
                mirror_with_mocked_put,
                slits,
                voltage_increment,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                inactive_slit_center,
                inactive_slit_size,
                number_of_slit_positions,
                bimorph_settle_time,
                initial_voltage_list,
            )
        )

        initial_voltage_list = initial_voltage_list or start_state.voltages

        assert [
            call(initial_voltage_list[i] + voltage_increment)
            == get_mock_put(channel.target_voltage).call_args
            for i, channel in enumerate(mirror_with_mocked_put.channels.values())
        ]

    async def test_bimorph_state_restored(
        self,
        mock_inner_scan: Mock,
        mock_move_slits: Mock,
        mock_restore_bimorph_state: Mock,
        mock_bps_sleep: Mock,
        mock_capture_bimorph_state: Mock,
        detectors: list[Readable],
        RE: RunEngine,
        mirror_with_mocked_put: BimorphMirror,
        slits: Slits,
        voltage_increment: float,
        active_dimension: SlitDimension,
        active_slit_center_start: float,
        active_slit_center_end: float,
        active_slit_size: float,
        inactive_slit_center: float,
        inactive_slit_size: float,
        number_of_slit_positions: int,
        bimorph_settle_time: float,
        initial_voltage_list: list[float],
        start_state: BimorphState,
    ):
        RE(
            bimorph_optimisation(
                detectors,
                mirror_with_mocked_put,
                slits,
                voltage_increment,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                inactive_slit_center,
                inactive_slit_size,
                number_of_slit_positions,
                bimorph_settle_time,
                initial_voltage_list,
            )
        )

        assert [
            call(mirror_with_mocked_put, slits, start_state)
        ] == mock_restore_bimorph_state.call_args_list


@pytest.mark.parametrize("voltage_increment", [100.0])
@pytest.mark.parametrize("active_dimension", [SlitDimension.X, SlitDimension.Y])
@pytest.mark.parametrize("active_slit_center_start", [0.0])
@pytest.mark.parametrize("active_slit_center_end", [200.0])
@pytest.mark.parametrize("active_slit_size", [0.05])
@pytest.mark.parametrize("inactive_slit_center", [0.0])
@pytest.mark.parametrize("inactive_slit_size", [0.05])
@pytest.mark.parametrize("number_of_slit_positions", [3])
@pytest.mark.parametrize("bimorph_settle_time", [0.0])
class TestIntegration:
    def test_full_plan(
        self,
        detectors: list[Readable],
        RE: RunEngine,
        mirror_with_mocked_put: BimorphMirror,
        slits: Slits,
        voltage_increment: float,
        active_dimension: SlitDimension,
        active_slit_center_start: float,
        active_slit_center_end: float,
        active_slit_size: float,
        inactive_slit_center: float,
        inactive_slit_size: float,
        number_of_slit_positions: int,
        bimorph_settle_time: float,
        initial_voltage_list: list[float],
    ):
        RE(
            bimorph_optimisation(
                detectors,
                mirror_with_mocked_put,
                slits,
                voltage_increment,
                active_dimension,
                active_slit_center_start,
                active_slit_center_end,
                active_slit_size,
                inactive_slit_center,
                inactive_slit_size,
                number_of_slit_positions,
                bimorph_settle_time,
                initial_voltage_list,
            )
        )

    assert True
