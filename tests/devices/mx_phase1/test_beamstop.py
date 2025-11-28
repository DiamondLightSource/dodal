from itertools import dropwhile
from unittest.mock import MagicMock, Mock, call

import pytest
from bluesky import FailedStatus
from bluesky import plan_stubs as bps
from bluesky.preprocessors import run_decorator
from bluesky.run_engine import RunEngine
from ophyd_async.core import get_mock, get_mock_put, set_mock_value

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.i03 import Beamstop, BeamstopPositions
from tests.common.beamlines.test_beamline_parameters import TEST_BEAMLINE_PARAMETERS_TXT


@pytest.fixture
def beamline_parameters() -> GDABeamlineParameters:
    return GDABeamlineParameters.from_file(TEST_BEAMLINE_PARAMETERS_TXT)


@pytest.mark.parametrize(
    "x, y, z, expected_pos",
    [
        [0, 0, 0, BeamstopPositions.UNKNOWN],
        [1.52, 44.78, 30.0, BeamstopPositions.DATA_COLLECTION],
        [1.501, 44.776, 29.71, BeamstopPositions.DATA_COLLECTION],
        [1.52, 42.78, 29.71, BeamstopPositions.OUT_OF_BEAM],
        [1.499, 44.776, 29.71, BeamstopPositions.UNKNOWN],
        [1.501, 44.774, 29.71, BeamstopPositions.UNKNOWN],
        [1.501, 44.776, 29.69, BeamstopPositions.UNKNOWN],
    ],
)
async def test_beamstop_pos_read_selected_pos(
    beamline_parameters: GDABeamlineParameters,
    run_engine: RunEngine,
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
    run_engine.subscribe(mock_callback, "event")

    @run_decorator()
    def check_in_beam():
        current_pos = yield from bps.rd(beamstop.selected_pos)
        assert current_pos == expected_pos
        yield from bps.create()
        yield from bps.read(beamstop)
        yield from bps.save()

    run_engine(check_in_beam())

    event_call = next(
        dropwhile(lambda c: c.args[0] != "event", mock_callback.mock_calls)
    )
    data = event_call.args[1]["data"]
    assert data["beamstop-x_mm"] == x
    assert data["beamstop-y_mm"] == y
    assert data["beamstop-z_mm"] == z
    assert data["beamstop-selected_pos"] == expected_pos


@pytest.mark.parametrize(
    "demanded_pos, expected_coords",
    [
        [BeamstopPositions.DATA_COLLECTION, (1.52, 44.78, 30.0)],
        [BeamstopPositions.OUT_OF_BEAM, (1.52, 42.78, 30.0)],
    ],
)
async def test_set_beamstop_position_to_data_collection_moves_beamstop(
    demanded_pos: BeamstopPositions,
    expected_coords: tuple[float, float, float],
    beamline_parameters: GDABeamlineParameters,
    run_engine: RunEngine,
):
    beamstop = Beamstop("-MO-BS-01:", beamline_parameters, name="beamstop")
    await beamstop.connect(mock=True)

    x_mock = beamstop.x_mm.user_setpoint
    y_mock = beamstop.y_mm.user_setpoint
    z_mock = beamstop.z_mm.user_setpoint

    parent_mock = MagicMock()
    parent_mock.attach_mock(get_mock_put(x_mock), "beamstop_x")
    parent_mock.attach_mock(get_mock_put(y_mock), "beamstop_y")
    parent_mock.attach_mock(get_mock_put(z_mock), "beamstop_z")

    run_engine(bps.abs_set(beamstop.selected_pos, demanded_pos, wait=True))

    assert get_mock_put(x_mock).call_args_list == [call(expected_coords[0], wait=True)]
    assert get_mock_put(y_mock).call_args_list == [call(expected_coords[1], wait=True)]
    assert get_mock_put(z_mock).call_args_list == [call(expected_coords[2], wait=True)]

    assert parent_mock.method_calls[0] == call.beamstop_z(30.0, wait=True)


async def test_set_beamstop_position_to_unknown_raises_error(
    beamline_parameters: GDABeamlineParameters, run_engine: RunEngine
):
    beamstop = Beamstop("-MO-BS-01:", beamline_parameters, name="beamstop")
    await beamstop.connect(mock=True)
    with pytest.raises(FailedStatus) as e:
        run_engine(
            bps.abs_set(beamstop.selected_pos, BeamstopPositions.UNKNOWN, wait=True)
        )
        assert isinstance(e.value.args[0].exception(), ValueError)


async def test_beamstop_select_pos_moves_z_axis_first(
    run_engine: RunEngine, beamline_parameters: GDABeamlineParameters
):
    beamstop = Beamstop("-MO-BS-01:", beamline_parameters, name="beamstop")
    await beamstop.connect(mock=True)

    run_engine(
        bps.abs_set(beamstop.selected_pos, BeamstopPositions.DATA_COLLECTION, wait=True)
    )

    parent = get_mock(beamstop)
    parent.assert_has_calls(
        [
            call.selected_pos.put(BeamstopPositions.DATA_COLLECTION, wait=True),
            call.z_mm.user_setpoint.put(30.0, wait=True),
            call.x_mm.user_setpoint.put(1.52, wait=True),
            call.y_mm.user_setpoint.put(44.78, wait=True),
        ]
    )
