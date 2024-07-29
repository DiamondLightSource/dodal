from __future__ import annotations

from typing import Any, cast

import bluesky.plan_stubs as bps
import pytest
from bluesky.callbacks import CallbackBase
from bluesky.run_engine import RunEngine
from event_model import Event
from ophyd_async.core import DeviceCollector

from dodal.devices.aperturescatterguard import (
    AperturePositions,
    ApertureScatterguard,
    InvalidApertureMove,
)

I03_BEAMLINE_PARAMETER_PATH = (
    "/dls_sw/i03/software/daq_configuration/domain/beamlineParameters"
)
BEAMLINE_PARAMETER_KEYWORDS = ["FB", "FULL", "deadtime"]


class GDABeamlineParameters:
    params: dict[str, Any]

    def __repr__(self) -> str:
        return repr(self.params)

    def __getitem__(self, item: str):
        return self.params[item]

    @classmethod
    def from_file(cls, path: str):
        ob = cls()
        with open(path) as f:
            config_lines = f.readlines()
        config_lines_nocomments = [line.split("#", 1)[0] for line in config_lines]
        config_lines_sep_key_and_value = [
            line.translate(str.maketrans("", "", " \n\t\r")).split("=")
            for line in config_lines_nocomments
        ]
        config_pairs: list[tuple[str, Any]] = [
            cast(tuple[str, Any], param)
            for param in config_lines_sep_key_and_value
            if len(param) == 2
        ]
        for i, (_, value) in enumerate(config_pairs):
            if value == "Yes":
                config_pairs[i] = (config_pairs[i][0], True)
            elif value == "No":
                config_pairs[i] = (config_pairs[i][0], False)
            elif value in BEAMLINE_PARAMETER_KEYWORDS:
                pass
            else:
                config_pairs[i] = (config_pairs[i][0], float(config_pairs[i][1]))
        ob.params = dict(config_pairs)
        return ob


@pytest.fixture
async def ap_sg():
    async with DeviceCollector():
        ap_sg = ApertureScatterguard(prefix="BL03S", name="ap_sg")
    ap_sg.load_aperture_positions(
        AperturePositions.from_gda_beamline_params(
            GDABeamlineParameters.from_file(I03_BEAMLINE_PARAMETER_PATH)
        )
    )
    return ap_sg


@pytest.fixture
def move_to_large(ap_sg: ApertureScatterguard):
    assert ap_sg.aperture_positions is not None
    yield from bps.abs_set(ap_sg, ap_sg.aperture_positions.LARGE)


@pytest.fixture
def move_to_medium(ap_sg: ApertureScatterguard):
    assert ap_sg.aperture_positions is not None
    yield from bps.abs_set(ap_sg, ap_sg.aperture_positions.MEDIUM)


@pytest.fixture
def move_to_small(ap_sg: ApertureScatterguard):
    assert ap_sg.aperture_positions is not None
    yield from bps.abs_set(ap_sg, ap_sg.aperture_positions.SMALL)


@pytest.fixture
def move_to_robotload(ap_sg: ApertureScatterguard):
    assert ap_sg.aperture_positions is not None
    yield from bps.abs_set(ap_sg, ap_sg.aperture_positions.ROBOT_LOAD)


@pytest.mark.s03
async def test_aperturescatterguard_setup(ap_sg: ApertureScatterguard):
    assert ap_sg.aperture_positions is not None


@pytest.mark.s03
async def test_aperturescatterguard_move_in_plan(
    ap_sg: ApertureScatterguard,
    move_to_large,
    move_to_medium,
    move_to_small,
    move_to_robotload,
    RE,
):
    assert ap_sg.aperture_positions is not None

    await ap_sg.aperture.z.set(ap_sg.aperture_positions.LARGE.location[2])

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
    assert ap_sg.aperture_positions
    positions = {
        "L": ap_sg.aperture_positions.LARGE,
        "M": ap_sg.aperture_positions.MEDIUM,
        "S": ap_sg.aperture_positions.SMALL,
        "R": ap_sg.aperture_positions.ROBOT_LOAD,
    }
    pos1 = positions[pos_name_1]
    pos2 = positions[pos_name_2]
    RE = RunEngine({})
    RE.subscribe(cb)

    await ap_sg.aperture.z.set(pos1.location[2])

    def monitor_and_moves():
        yield from bps.open_run()
        yield from bps.monitor(ap_sg.aperture.y.motor_done_move, name="ap_y")
        yield from bps.monitor(ap_sg.scatterguard.y.motor_done_move, name="sg_y")
        yield from bps.mv(ap_sg, pos1)
        yield from bps.mv(ap_sg, pos2)
        yield from bps.close_run()

    RE(monitor_and_moves())

    assert cb.t_sg_y
    assert cb.t_ap_y
    assert (cb.t_sg_y < cb.t_ap_y) == sg_first
