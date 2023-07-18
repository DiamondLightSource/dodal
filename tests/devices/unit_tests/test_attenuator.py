from unittest.mock import MagicMock

import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from ophyd.sim import make_fake_device
from ophyd.status import Status

from dodal.devices.attenuator import Attenuator

CALCULATED_VALUE = range(0, 17)


@pytest.fixture
def fake_attenuator():
    FakeAttenuator: Attenuator = make_fake_device(Attenuator)
    fake_attenuator: Attenuator = FakeAttenuator(name="attenuator")

    def mock_apply_values(val: int):
        actual_states = fake_attenuator.get_actual_filter_state_list()
        calculated_states = fake_attenuator.get_calculated_filter_state_list()
        for i in range(16):
            calculated_states[i].sim_put(
                CALCULATED_VALUE[i]
            )  # Ignore the actual calculation as this is EPICS layer
            actual_states[i].sim_put(calculated_states[i].get())
        return Status(done=True, success=True)

    fake_attenuator.change.set = MagicMock(side_effect=mock_apply_values)

    return fake_attenuator


def test_set_transmission_success(fake_attenuator: Attenuator):
    fake_attenuator.set(1.0).wait(1)


def test_set_transmission_in_run_engine(fake_attenuator: Attenuator):
    RE = RunEngine()
    RE(bps.abs_set(fake_attenuator, 1, wait=True))
