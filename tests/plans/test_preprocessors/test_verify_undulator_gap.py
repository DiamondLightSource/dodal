from unittest.mock import MagicMock, patch

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky.run_engine import RunEngine
from tests.plans.conftest import UndulatorGapCheckDevices

from dodal.plans.preprocessors.verify_undulator_gap import (
    verify_undulator_gap_before_run_decorator,
)

RUN_KEY = "test_run"


@patch("dodal.plans.verify_undulator_gap.verify_undulator_gap")
def test_verify_undulator_gap_decorator_does_nothing_on_wrong_run(
    mock_verify: MagicMock,
    RE: RunEngine,
    mock_undulator_and_dcm: UndulatorGapCheckDevices,
):
    @verify_undulator_gap_before_run_decorator(
        devices=mock_undulator_and_dcm, run_key_to_wrap=RUN_KEY
    )
    def boring_plan():
        yield from bps.null()

    RE(boring_plan())
    mock_verify.assert_not_called()


@patch("dodal.plans.preprocessors.verify_undulator_gap.verify_undulator_gap")
def test_verify_undulator_gap_decorator_runs_on_run_key_only(
    mock_verify: MagicMock,
    RE: RunEngine,
    mock_undulator_and_dcm: UndulatorGapCheckDevices,
):
    @verify_undulator_gap_before_run_decorator(
        devices=mock_undulator_and_dcm, run_key_to_wrap=RUN_KEY
    )
    @bpp.run_decorator()
    def outer_plan():
        mock_verify.assert_not_called()
        yield from plan_with_run_key()

    @bpp.set_run_key_decorator(RUN_KEY)
    @bpp.run_decorator()
    def plan_with_run_key():
        mock_verify.assert_called_once()
        yield from inner_plan()

    def inner_plan():
        yield from bps.null()

    RE(outer_plan())
    mock_verify.assert_called_once()


@patch("dodal.plans.preprocessors.verify_undulator_gap.verify_undulator_gap")
def test_verify_undulator_gap_decorator_no_run_key_runs_on_first_run_only(
    mock_verify: MagicMock,
    RE: RunEngine,
    mock_undulator_and_dcm: UndulatorGapCheckDevices,
):
    @verify_undulator_gap_before_run_decorator(devices=mock_undulator_and_dcm)
    @bpp.run_decorator()
    def outer_plan():
        mock_verify.assert_called_once()
        yield from plan_with_run()

    @bpp.set_run_key_decorator(RUN_KEY)
    @bpp.run_decorator()
    def plan_with_run():
        yield from inner_plan()

    def inner_plan():
        yield from bps.null()

    RE(outer_plan())
    mock_verify.assert_called_once()
