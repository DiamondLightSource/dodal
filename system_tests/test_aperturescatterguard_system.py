from __future__ import annotations

import bluesky.plan_stubs as bps
import pytest
from bluesky.callbacks import CallbackBase
from bluesky.run_engine import RunEngine
from event_model import Event
from ophyd_async.core import DeviceCollector

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.aperturescatterguard import (
    AperturePosition,
    ApertureScatterguard,
    ApertureValue,
    InvalidApertureMove,
    load_positions_from_beamline_parameters,
)

I03_BEAMLINE_PARAMETER_PATH = (
    "/dls_sw/i03/software/daq_configuration/domain/beamlineParameters"
)
BEAMLINE_PARAMETER_KEYWORDS = ["FB", "FULL", "deadtime"]


@pytest.fixture
async def ap_sg():
    params = GDABeamlineParameters.from_file(I03_BEAMLINE_PARAMETER_PATH)
    positions = load_positions_from_beamline_parameters(params)
    tolerances = AperturePosition.tolerances_from_gda_params(params)

    async with DeviceCollector():
        ap_sg = ApertureScatterguard(
            prefix="BL03S",
            name="ap_sg",
            loaded_positions=positions,
            tolerances=tolerances,
        )
    return ap_sg


@pytest.fixture
def move_to_large(ap_sg: ApertureScatterguard):
    assert ap_sg._loaded_positions is not None
    yield from bps.abs_set(ap_sg, ApertureValue.LARGE)


@pytest.fixture
def move_to_medium(ap_sg: ApertureScatterguard):
    assert ap_sg._loaded_positions is not None
    yield from bps.abs_set(ap_sg, ApertureValue.MEDIUM)


@pytest.fixture
def move_to_small(ap_sg: ApertureScatterguard):
    assert ap_sg._loaded_positions is not None
    yield from bps.abs_set(ap_sg, ApertureValue.SMALL)


@pytest.fixture
def move_to_robotload(ap_sg: ApertureScatterguard):
    assert ap_sg._loaded_positions is not None
    yield from bps.abs_set(ap_sg, ApertureValue.ROBOT_LOAD)


@pytest.mark.s03
async def test_aperturescatterguard_setup(ap_sg: ApertureScatterguard):
    assert ap_sg._loaded_positions is not None


@pytest.mark.s03
async def test_aperturescatterguard_move_in_plan(
    ap_sg: ApertureScatterguard,
    move_to_large,
    move_to_medium,
    move_to_small,
    move_to_robotload,
    RE,
):
    assert ap_sg._loaded_positions is not None
    large = ap_sg._loaded_positions[ApertureValue.LARGE]

    await ap_sg.aperture.z.set(large.aperture_z)

    RE(move_to_large)
    RE(move_to_medium)
    RE(move_to_small)
    RE(move_to_robotload)


@pytest.mark.s03
async def test_move_fails_when_not_in_good_starting_pos(
    ap_sg: ApertureScatterguard, move_to_large, RE
):
    await ap_sg.aperture.z.set(0)

    with pytest.raises(InvalidApertureMove):
        RE(move_to_large)


class MonitorCallback(CallbackBase):
    # holds on to the most recent time a motor move completed for aperture and
    # scatterguard y

    t_ap_y: float | None = 0
    t_sg_y: float | None = 0
    event_docs: list[Event] = []

    def event(self, doc):
        self.event_docs.append(doc)
        if doc["data"].get("ap_sg_aperture_y_motor_done_move") == 1:
            self.t_ap_y = doc["timestamps"].get("ap_sg_aperture_y_motor_done_move")
        if doc["data"].get("ap_sg_scatterguard_y_motor_done_move") == 1:
            self.t_sg_y = doc["timestamps"].get("ap_sg_scatterguard_y_motor_done_move")
        return doc


@pytest.mark.s03
@pytest.mark.parametrize(
    "pos_name_1,pos_name_2,sg_first",
    [
        ("L", "M", True),
        ("L", "S", True),
        ("L", "R", False),
        ("M", "L", False),
        ("M", "S", True),
        ("M", "R", False),
        ("S", "L", False),
        ("S", "M", False),
        ("S", "R", False),
        ("R", "L", True),
        ("R", "M", True),
        ("R", "S", True),
    ],
)
async def test_aperturescatterguard_moves_in_correct_order(
    pos_name_1, pos_name_2, sg_first, ap_sg: ApertureScatterguard
):
    cb = MonitorCallback()
    assert ap_sg._loaded_positions
    positions = {
        "L": ap_sg._loaded_positions[ApertureValue.LARGE],
        "M": ap_sg._loaded_positions[ApertureValue.MEDIUM],
        "S": ap_sg._loaded_positions[ApertureValue.SMALL],
        "R": ap_sg._loaded_positions[ApertureValue.ROBOT_LOAD],
    }
    pos1 = positions[pos_name_1]
    pos2 = positions[pos_name_2]
    RE = RunEngine({})
    RE.subscribe(cb)

    await ap_sg.aperture.z.set(pos1.aperture_z)

    def monitor_and_moves():
        yield from bps.open_run()
        yield from bps.monitor(ap_sg.aperture.y.motor_done_move, name="ap_y")
        yield from bps.monitor(ap_sg.scatterguard.y.motor_done_move, name="sg_y")
        yield from bps.mv(ap_sg, pos1)  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
        yield from bps.mv(ap_sg, pos2)  # type: ignore # See: https://github.com/DiamondLightSource/dodal/issues/827
        yield from bps.close_run()

    RE(monitor_and_moves())

    assert cb.t_sg_y
    assert cb.t_ap_y
    assert (cb.t_sg_y < cb.t_ap_y) == sg_first
