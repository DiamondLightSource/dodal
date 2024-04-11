from unittest.mock import ANY

import pytest
from ophyd_async.core import DeviceCollector, set_sim_value

from dodal.devices.s4_slit_gaps import S4SlitGaps, S4SlitGapsGroup


@pytest.fixture
async def slits() -> S4SlitGaps:
    async with DeviceCollector(sim=True):
        slits = S4SlitGaps("DEMO-SLITS-01:")

    return slits


@pytest.fixture
async def slit_group() -> S4SlitGapsGroup:
    async with DeviceCollector(sim=True):
        slit_group = S4SlitGapsGroup("DEMO-SLITS-{0:02d}:", range(2, 5))

    return slit_group


async def test_slit_group_creates_slits_with_correct_prefixes(
    slit_group: S4SlitGapsGroup,
):
    expected_prefixes = {
        2: "DEMO-SLITS-02:",
        3: "DEMO-SLITS-03:",
        4: "DEMO-SLITS-04:",
    }

    for index, prefix in expected_prefixes.items():
        sim_pv = slit_group.slits[index].x_gap.readback.source
        assert sim_pv == f"sim://{prefix}X:SIZE.RBV"


async def test_reading_slits_reads_gaps_and_centres(slits: S4SlitGaps):
    set_sim_value(slits.x_gap.readback, 0.5)
    set_sim_value(slits.y_centre.readback, 1.0)
    set_sim_value(slits.y_gap.readback, 1.5)

    await slits.stage()
    reading = await slits.read()
    await slits.unstage()

    assert reading == {
        "slits-x_centre": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "slits-x_gap": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.5,
        },
        "slits-y_centre": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 1.0,
        },
        "slits-y_gap": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 1.5,
        },
    }


async def test_reading_slit_group_reads_gaps_and_centres(slit_group: S4SlitGapsGroup):
    await slit_group.stage()
    reading = await slit_group.read()
    await slit_group.unstage()

    assert reading == {
        "slit_group-slits-2-x_centre": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "slit_group-slits-2-x_gap": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "slit_group-slits-2-y_centre": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "slit_group-slits-2-y_gap": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "slit_group-slits-3-x_centre": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "slit_group-slits-3-x_gap": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "slit_group-slits-3-y_centre": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "slit_group-slits-3-y_gap": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "slit_group-slits-4-x_centre": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "slit_group-slits-4-x_gap": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "slit_group-slits-4-y_centre": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "slit_group-slits-4-y_gap": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
    }
