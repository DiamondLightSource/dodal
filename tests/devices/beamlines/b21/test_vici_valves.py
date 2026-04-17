import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.b21.vici_valves import (
    Valve1Positions,
    Valve2Positions,
    ViciValves,
)


@pytest.fixture
async def vici_valves() -> ViciValves:
    async with init_devices(mock=True):
        valves = ViciValves("", "")
    return valves


async def test_vici_valves_read(
    vici_valves: ViciValves,
):
    set_mock_value(vici_valves.valve_1, Valve1Positions.POS_1)
    set_mock_value(vici_valves.valve_2, Valve2Positions.POS_2)

    await assert_reading(
        vici_valves,
        {
            f"{vici_valves.name}-valve_1": partial_reading(Valve1Positions.POS_1),
            f"{vici_valves.name}-valve_2": partial_reading(Valve2Positions.POS_2),
        },
    )
