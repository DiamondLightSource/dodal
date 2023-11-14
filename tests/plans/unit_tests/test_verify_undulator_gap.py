from unittest.mock import patch

import pytest
from ophyd.sim import make_fake_device

from dodal.beamlines.beamline_utils import device_instantiation
from dodal.devices.DCM import DCM
from dodal.devices.undulator import Undulator
from dodal.plans.verify_undulator_gap import UndulatorGapAccess, verify_undulator_gap

# @pytest.fixture
# def fake_devices():
#     xbpm_feedback: XBPMFeedback = make_fake_device(XBPMFeedback)(name="xbpm")
#     attenuator: Attenuator = make_fake_device(Attenuator)(name="atten")

#     def fake_attenuator_set(val):
#         attenuator.actual_transmission.sim_put(val)
#         return Status(done=True, success=True)

#     attenuator.set = MagicMock(side_effect=fake_attenuator_set)

#     return xbpm_feedback, attenuator


@pytest.fixture
def fake_undulator() -> Undulator:
    undulator = make_fake_device(Undulator)(name="undulator")
    return undulator


@pytest.fixture
def fake_dcm() -> DCM:
    dcm = make_fake_device(DCM)(name="dcm")
    return dcm


@patch("dodal.plans.verify_undulator_gap.LOGGER")
def test_when_gap_access_is_disabled_function_returns_false_and_logger_gives_warning(
    mock_logger, fake_dcm: DCM, fake_undulator: Undulator
):
    fake_undulator.gap_access.sim_put(UndulatorGapAccess.DISABLED.value)
    assert (
        verify_undulator_gap(fake_undulator, fake_dcm, fake_undulator.lookup_table_path)
        is False
    )
    mock_logger.warning.assert_called_once()


def test_energy_to_distance_table_correct_format():
    ...


def test_correct_closest_distance_to_energy_from_table():
    ...


def test_if_gap_is_wrong_then_logger_warning_and_gap_is_set():
    ...


def test_if_gap_is_correct_then_return_true():
    ...
