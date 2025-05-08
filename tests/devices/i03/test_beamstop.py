from itertools import dropwhile
from unittest.mock import Mock

import pytest
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
