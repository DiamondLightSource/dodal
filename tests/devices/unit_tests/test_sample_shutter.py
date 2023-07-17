from unittest.mock import MagicMock

import pytest
from ophyd.sim import make_fake_device

from dodal.devices.sample_shutter import OpenState, SampleShutter


@pytest.fixture
def fake_sample_shutter():
    FakeSampleShutter: SampleShutter = make_fake_device(SampleShutter)
    fake_sample_shutter: SampleShutter = FakeSampleShutter(name="sample_shutter")
    return fake_sample_shutter


def set_pos_rbv(fake_sample_shutter: SampleShutter, value):
    fake_sample_shutter.pos_rbv.sim_put(value)


@pytest.mark.parametrize(
    "state",
    [
        (OpenState.OPEN),
        (OpenState.CLOSE),
    ],
)
def test_set_opens_and_closes_shutter(state, fake_sample_shutter):
    status = fake_sample_shutter.set(state)
    status_finished = MagicMock()
    status.add_callback(status_finished)
    status_finished.assert_not_called()
    set_pos_rbv(fake_sample_shutter, state)
    status.wait(1)
