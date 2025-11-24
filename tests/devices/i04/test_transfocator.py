import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from bluesky.protocols import Reading
from ophyd_async.core import set_mock_value, wait_for_value

from dodal.devices.i04.transfocator import Transfocator


def given_predicted_lenses_is_half_of_beamsize(transfocator: Transfocator):
    def lens_number_is_half_beamsize(
        reading: dict[str, Reading[float]], *args, **kwargs
    ):
        value = reading[transfocator._vert_size_calc_sp.name]["value"]
        set_mock_value(transfocator._num_lenses_calc_rbv, int(value / 2))

    transfocator._vert_size_calc_sp.subscribe_reading(lens_number_is_half_beamsize)


async def set_beamsize_to_same_value_as_mock_signal(
    transfocator: Transfocator, value: float
):
    set_mock_value(transfocator._num_lenses_calc_rbv, value)
    await transfocator.set(value)


@patch("dodal.devices.i04.transfocator.wait_for_value")
async def test_when_beamsize_set_then_set_correctly_on_device_and_waited_on(
    mock_wait_for_value,
    fake_transfocator: Transfocator,
):
    given_predicted_lenses_is_half_of_beamsize(fake_transfocator)
    set_status = fake_transfocator.set(315)

    assert not set_status.done

    await asyncio.gather(
        wait_for_value(fake_transfocator._num_lenses_calc_rbv, 157, 0.1),
        wait_for_value(fake_transfocator.number_filters_sp, 157, 0.1),
        wait_for_value(fake_transfocator.start, 1, 0.1),
    )

    await set_status
    assert set_status.done and set_status.success


async def test_if_timeout_exceeded_and_start_rbv_not_equal_to_set_value_then_timeout_exception(
    fake_transfocator: Transfocator,
) -> None:
    with patch.object(fake_transfocator, "TIMEOUT", 0):
        given_predicted_lenses_is_half_of_beamsize(fake_transfocator)
        fake_transfocator.start_rbv.get_value = AsyncMock(side_effect=[0, 1])
        with pytest.raises(TimeoutError):
            await fake_transfocator.set(315)
