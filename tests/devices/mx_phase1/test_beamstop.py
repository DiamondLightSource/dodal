from itertools import dropwhile
from unittest.mock import AsyncMock, Mock

import pytest
from bluesky import FailedStatus
from bluesky import plan_stubs as bps
from bluesky.preprocessors import run_decorator
from bluesky.run_engine import RunEngine
from ophyd_async.testing import set_mock_value

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.i03 import Beamstop, BeamstopPositions


@pytest.fixture
def beamline_parameters() -> GDABeamlineParameters:
    return GDABeamlineParameters.from_file(
        "tests/test_data/test_beamline_parameters.txt"
    )


@pytest.mark.parametrize(
    "x, y, z, expected_pos",
    [
        [0, 0, 0, BeamstopPositions.UNKNOWN],
        [1.52, 44.78, 30.0, BeamstopPositions.DATA_COLLECTION],
        [1.501, 44.776, 29.71, BeamstopPositions.DATA_COLLECTION],
        [1.499, 44.776, 29.71, BeamstopPositions.UNKNOWN],
        [1.501, 44.774, 29.71, BeamstopPositions.UNKNOWN],
        [1.501, 44.776, 29.69, BeamstopPositions.UNKNOWN],
    ],
)
async def test_beamstop_pos_select(
    beamline_parameters: GDABeamlineParameters,
    RE: RunEngine,
    x: float,
    y: float,
    z: float,
    expected_pos: BeamstopPositions,
):
    beamstop = Beamstop("-MO-BS-01:", beamline_parameters, name="beamstop")
    await beamstop.connect(mock=True)
    set_mock_value(beamstop.x_mm.user_readback, x)
    set_mock_value(beamstop.y_mm.user_readback, y)
    set_mock_value(beamstop.z_mm.user_readback, z)

    mock_callback = Mock()
    RE.subscribe(mock_callback, "event")

    @run_decorator()
    def check_in_beam():
        current_pos = yield from bps.rd(beamstop.selected_pos)
        assert current_pos == expected_pos
        yield from bps.create()
        yield from bps.read(beamstop)
        yield from bps.save()

    RE(check_in_beam())

    event_call = next(
        dropwhile(lambda c: c.args[0] != "event", mock_callback.mock_calls)
    )
    data = event_call.args[1]["data"]
    assert data["beamstop-x_mm"] == x
    assert data["beamstop-y_mm"] == y
    assert data["beamstop-z_mm"] == z
    assert data["beamstop-selected_pos"] == expected_pos


async def test_set_beamstop_position_to_data_collection_moves_beamstop_into_beam(
    beamline_parameters: GDABeamlineParameters, RE: RunEngine
):
    beamstop = Beamstop("-MO-BS-01:", beamline_parameters, name="beamstop")
    await beamstop.connect(mock=True)

    beamstop.x_mm.set = AsyncMock()
    beamstop.y_mm.set = AsyncMock()
    beamstop.z_mm.set = AsyncMock()
    set_mock_value(beamstop.x_mm.user_readback, 0)
    set_mock_value(beamstop.y_mm.user_readback, 0)
    set_mock_value(beamstop.z_mm.user_readback, 0)

    RE(bps.abs_set(beamstop.selected_pos, BeamstopPositions.DATA_COLLECTION))

    assert beamstop.x_mm.set.call_count == 1
    assert beamstop.x_mm.set.call_args[0][0] == 1.52

    assert beamstop.y_mm.set.call_count == 1
    assert beamstop.y_mm.set.call_args[0][0] == 44.78

    assert beamstop.z_mm.set.call_count == 1
    assert beamstop.z_mm.set.call_args[0][0] == 30.0


async def test_set_beamstop_position_to_unknown_raises_error(
    beamline_parameters: GDABeamlineParameters, RE: RunEngine
):
    beamstop = Beamstop("-MO-BS-01:", beamline_parameters, name="beamstop")
    await beamstop.connect(mock=True)
    with pytest.raises(FailedStatus) as e:
        RE(bps.abs_set(beamstop.selected_pos, BeamstopPositions.UNKNOWN, wait=True))
        assert isinstance(e.value.args[0].exception(), ValueError)
