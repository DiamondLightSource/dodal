from unittest.mock import MagicMock, patch

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import set_mock_value

from dodal.beamlines import i03
from dodal.devices.synchrotron import Synchrotron, SynchrotronMode
from dodal.plans.check_topup import (
    check_topup_and_wait_if_necessary,
    wait_for_topup_complete,
)


@pytest.fixture
def synchrotron(RE) -> Synchrotron:
    return i03.synchrotron(fake_with_ophyd_sim=True)


@patch("dodal.plans.check_topup.wait_for_topup_complete")
@patch("dodal.plans.check_topup.bps.sleep")
def test_when_topup_before_end_of_collection_wait(
    fake_sleep: MagicMock, fake_wait: MagicMock, synchrotron: Synchrotron, RE: RunEngine
):
    set_mock_value(synchrotron.synchrotron_mode, SynchrotronMode.USER)
    set_mock_value(synchrotron.topup_start_countdown, 20.0)
    set_mock_value(synchrotron.top_up_end_countdown, 60.0)

    RE(
        check_topup_and_wait_if_necessary(
            synchrotron=synchrotron,
            total_exposure_time=40.0,
            ops_time=30.0,
        )
    )
    fake_sleep.assert_called_once_with(60.0)


@patch("dodal.plans.check_topup.bps.rd")
@patch("dodal.plans.check_topup.bps.sleep")
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


@patch("dodal.plans.check_topup.bps.sleep")
@patch("dodal.plans.check_topup.bps.null")
def test_no_waiting_if_decay_mode(
    fake_null: MagicMock, fake_sleep: MagicMock, synchrotron: Synchrotron, RE: RunEngine
):
    set_mock_value(synchrotron.topup_start_countdown, -1)

    RE(
        check_topup_and_wait_if_necessary(
            synchrotron=synchrotron,
            total_exposure_time=10.0,
            ops_time=1.0,
        )
    )
    fake_null.assert_called_once()
    assert fake_sleep.call_count == 0


@patch("dodal.plans.check_topup.bps.null")
def test_no_waiting_when_mode_does_not_allow_gating(
    fake_null: MagicMock, synchrotron: Synchrotron, RE: RunEngine
):
    set_mock_value(synchrotron.topup_start_countdown, 1.0)
    set_mock_value(synchrotron.synchrotron_mode, SynchrotronMode.SHUTDOWN)

    RE(
        check_topup_and_wait_if_necessary(
            synchrotron=synchrotron,
            total_exposure_time=10.0,
            ops_time=1.0,
        )
    )
    fake_null.assert_called_once()
