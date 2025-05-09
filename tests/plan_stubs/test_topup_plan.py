from unittest.mock import MagicMock, patch

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.synchrotron import Synchrotron, SynchrotronMode
from dodal.plan_stubs.check_topup import (
    check_topup_and_wait_if_necessary,
    wait_for_topup_complete,
)


@pytest.fixture
async def synchrotron(RE) -> Synchrotron:
    async with init_devices(mock=True):
        synchrotron = Synchrotron()
    return synchrotron


@patch("dodal.plan_stubs.check_topup.wait_for_topup_complete")
@patch("dodal.plan_stubs.check_topup.bps.sleep")
def test_when_topup_before_end_of_collection_wait(
    fake_sleep: MagicMock, fake_wait: MagicMock, synchrotron: Synchrotron, RE: RunEngine
):
    set_mock_value(synchrotron.synchrotron_mode, SynchrotronMode.USER)
    set_mock_value(synchrotron.top_up_start_countdown, 20.0)
    set_mock_value(synchrotron.top_up_end_countdown, 60.0)

    RE(
        check_topup_and_wait_if_necessary(
            synchrotron=synchrotron,
            total_exposure_time=40.0,
            ops_time=30.0,
        )
    )
    fake_sleep.assert_called_once_with(61.0)


@patch("dodal.plan_stubs.check_topup.bps.rd")
@patch("dodal.plan_stubs.check_topup.bps.sleep")
def test_wait_for_topup_complete(
    fake_sleep: MagicMock, fake_rd: MagicMock, synchrotron: Synchrotron, RE: RunEngine
):
    def fake_generator(value):
        yield from bps.null()
        return value

    fake_rd.side_effect = [
        fake_generator(0.0),
        fake_generator(0.0),
        fake_generator(0.0),
        fake_generator(10.0),
    ]

    RE(wait_for_topup_complete(synchrotron))

    assert fake_sleep.call_count == 3
    fake_sleep.assert_called_with(0.1)


@patch("dodal.plan_stubs.check_topup.bps.sleep")
@patch("dodal.plan_stubs.check_topup.bps.null")
def test_no_waiting_if_decay_mode(
    fake_null: MagicMock, fake_sleep: MagicMock, synchrotron: Synchrotron, RE: RunEngine
):
    set_mock_value(synchrotron.top_up_start_countdown, -1)

    RE(
        check_topup_and_wait_if_necessary(
            synchrotron=synchrotron,
            total_exposure_time=10.0,
            ops_time=1.0,
        )
    )
    fake_null.assert_called_once()
    assert fake_sleep.call_count == 0


@patch("dodal.plan_stubs.check_topup.bps.null")
def test_no_waiting_when_mode_does_not_allow_gating(
    fake_null: MagicMock, synchrotron: Synchrotron, RE: RunEngine
):
    set_mock_value(synchrotron.top_up_start_countdown, 1.0)
    set_mock_value(synchrotron.synchrotron_mode, SynchrotronMode.SHUTDOWN)

    RE(
        check_topup_and_wait_if_necessary(
            synchrotron=synchrotron,
            total_exposure_time=10.0,
            ops_time=1.0,
        )
    )
    fake_null.assert_called_once()


@pytest.mark.parametrize(
    "topup_start_countdown, topup_end_countdown, total_exposure_time, ops_time,"
    "expected_wait, parameter_file",
    # limit = 120, delay = 1
    [
        (100, 108, 121, 1, 0, "test_beamline_parameters.txt"),
        (100, 108, 119, 1, 108 + 1, "test_beamline_parameters.txt"),
        (110, 120, 120, 1, 0, "test_beamline_parameters.txt"),
        (110.1, 120, 119.99, 1, 120 + 1, "test_beamline_parameters.txt"),
        # limit = 35, delay = 1
        (110.1, 120, 36, 1, 0, "topup_short_params.txt"),
        (36, 42, 36, 1, 0, "topup_short_params.txt"),
        (36, 42, 34, 4, 42 + 1, "topup_short_params.txt"),
        (36, 42, 34, 2, 0, "topup_short_params.txt"),
        (36, 42, 35, 3, 0, "topup_short_params.txt"),
        (31.1, 39, 31, 1, 39 + 1, "topup_short_params.txt"),
        (30.1, 38, 31, 1, 38 + 1, "topup_short_params.txt"),
        # limit = 30, delay = 19
        (30, 40, 29, 1, 0, "topup_long_delay.txt"),
        (29, 39, 29, 1, 39 + 19, "topup_long_delay.txt"),
        (29, 39, 28, 1, 0, "topup_long_delay.txt"),
        (29, 39, 28, 2, 39 + 19, "topup_long_delay.txt"),
        (29, 39, 27, 2, 0, "topup_long_delay.txt"),
        (29, 39, 35, 1, 0, "topup_long_delay.txt"),
    ],
)
@patch("dodal.plan_stubs.check_topup.bps.sleep")
def test_topup_not_allowed_when_exceeds_threshold_percentage_of_topup_time(
    mock_sleep,
    RE: RunEngine,
    synchrotron: Synchrotron,
    topup_start_countdown: float,
    topup_end_countdown: float,
    total_exposure_time: float,
    ops_time: float,
    expected_wait: float,
    parameter_file: str,
):
    set_mock_value(synchrotron.synchrotron_mode, SynchrotronMode.USER)
    set_mock_value(synchrotron.top_up_start_countdown, topup_start_countdown)
    set_mock_value(synchrotron.top_up_end_countdown, topup_end_countdown)

    with patch(
        "dodal.common.beamlines.beamline_parameters.BEAMLINE_PARAMETER_PATHS",
        {"i03": f"tests/test_data/{parameter_file}"},
    ):
        RE(
            check_topup_and_wait_if_necessary(
                synchrotron, total_exposure_time, ops_time
            )
        )

    mock_sleep.assert_called_with(expected_wait)
