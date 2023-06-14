from unittest.mock import MagicMock

import pytest
from ophyd.sim import make_fake_device
from ophyd.status import Status

from dodal.devices.attenuator.attenuator import Attenuator

CALCULATED_VALUE = 10


@pytest.fixture
def fake_attenuator():
    FakeAttenuator: Attenuator = make_fake_device(Attenuator)
    fake_attenuator: Attenuator = FakeAttenuator(name="aperture")

    def mock_apply_values(val: int):
        actual_states = fake_attenuator.get_actual_filter_state_list()
        calculated_states = fake_attenuator.get_calculated_filter_state_list()
        for i in range(16):
            calculated_states[i].sim_put(
                CALCULATED_VALUE
            )  # Ignore the actual calculation as this is EPICS layer
            actual_states[i].sim_put(calculated_states[i].get())
        return Status(done=True, success=True)

    fake_attenuator.change.set = MagicMock(side_effect=mock_apply_values)

    return fake_attenuator


def test_set_transmission_success(fake_attenuator: Attenuator):
    fake_attenuator.calulated_filter_state_10.sim_put(1)
    fake_attenuator.set_transmission(1.0).wait(10)
