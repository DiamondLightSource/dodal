from unittest.mock import MagicMock, patch
import asyncio
import pytest
from ophyd.sim import make_fake_device
from ophyd.status import SubscriptionStatus

from ophyd_async.core import (
    DeviceCollector,
    set_mock_value,
    AsyncStatus,
)

from dodal.devices.i04.transfocator import Transfocator

@pytest.fixture
async def fake_transfocator() -> Transfocator:
    async with DeviceCollector(mock=True):
        transfocator = Transfocator(prefix="", name="transfocator")
    return transfocator

def given_predicted_lenses_is_half_of_beamsize(transfocator: Transfocator):
    def lens_number_is_half_beamsize(value, *args, **kwargs):
        set_mock_value(transfocator.predicted_vertical_num_lenses, int(value / 2))

    transfocator.beamsize_set_microns.subscribe(lens_number_is_half_beamsize)


async def test_given_beamsize_already_set_then_when_transfocator_set_then_returns_immediately(
    fake_transfocator: Transfocator,
):
    async with asyncio.timeout(0.01):
        set_mock_value(fake_transfocator.beamsize_set_microns, 100.0)
        await fake_transfocator.set(100.0)

@patch("dodal.devices.i04.transfocator.sleep")
def test_when_beamsize_set_then_set_correctly_on_device_and_waited_on(
    mock_sleep,
    fake_transfocator: Transfocator,
):
    given_predicted_lenses_is_half_of_beamsize(fake_transfocator)

    transfocator_statuses = SubscriptionStatus(
        fake_transfocator.predicted_vertical_num_lenses,
        lambda *, old_value, value, **kwargs: value == 157,
    )
    transfocator_statuses &= SubscriptionStatus(
        fake_transfocator.number_filters_sp,
        lambda *, old_value, value, **kwargs: value == 157,
    )
    transfocator_statuses &= SubscriptionStatus(
        fake_transfocator.start,
        lambda *, old_value, value, **kwargs: value == 1,
    )

    set_status = fake_transfocator.set(315)

    transfocator_statuses.wait(0.1)
    assert not set_status.done

    fake_transfocator.start_rbv.get = MagicMock(side_effect=[1, 0])

    set_status.wait(0.1)
    assert set_status.done and set_status.success

    try:
        transfocator_statuses.wait(0.1)
    except BaseException:
        pass
