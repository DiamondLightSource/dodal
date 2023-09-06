from unittest.mock import MagicMock, patch

import pytest
from ophyd.sim import make_fake_device

from dodal.devices.i04.transfocator import Transfocator


@pytest.fixture
def fake_transfocator():
    FakeTransfocator = make_fake_device(Transfocator)
    transfocator: Transfocator = FakeTransfocator(name="test_transfocator")
    yield transfocator


def given_predicted_lenses_is_half_of_beamsize(transfocator: Transfocator):
    def lens_number_is_half_beamsize(value, *args, **kwargs):
        transfocator.predicted_vertical_num_lenses.sim_put(int(value / 2))

    transfocator.beamsize_set_microns.subscribe(lens_number_is_half_beamsize)


def test_given_beamsize_already_set_then_when_transfocator_set_then_returns_immediately(
    fake_transfocator: Transfocator,
):
    fake_transfocator.beamsize_set_microns.sim_put(100)
    set_status = fake_transfocator.set(100)
    set_status.wait(0.01)
    assert set_status.done and set_status.success


@patch("dodal.devices.i04.transfocator.sleep")
def test_when_beamsize_set_then_set_correctly_on_device_and_waited_on(
    mock_sleep,
    fake_transfocator: Transfocator,
):
    given_predicted_lenses_is_half_of_beamsize(fake_transfocator)

    set_status = fake_transfocator.set(315)

    from time import sleep

    sleep(0.01)

    assert fake_transfocator.predicted_vertical_num_lenses.get() == 157
    assert fake_transfocator.number_filters_sp.get() == 157
    assert fake_transfocator.start.get() == 1

    assert not set_status.done

    fake_transfocator.start_rbv.get = MagicMock(side_effect=[1, 0])

    set_status.wait(0.01)
    assert set_status.done and set_status.success
