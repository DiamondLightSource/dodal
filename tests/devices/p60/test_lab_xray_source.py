import re

import pytest
from bluesky.plan_stubs import mv
from bluesky.protocols import Movable
from bluesky.run_engine import RunEngine
from ophyd_async.core import StandardReadable, init_devices
from ophyd_async.testing import assert_value

from dodal.devices.p60.lab_xray_source import LabXraySource, LabXraySourceReadable


@pytest.fixture
async def al_kalpha_source() -> LabXraySourceReadable:
    async with init_devices():
        al_kalpha_source = LabXraySourceReadable(LabXraySource.AL_KALPHA)
    return al_kalpha_source


@pytest.fixture
async def al_kalpha_source_signal_name(al_kalpha_source: LabXraySourceReadable) -> str:
    return f"{al_kalpha_source.name}-energy_ev"


@pytest.fixture
async def mg_kalpha_source() -> LabXraySourceReadable:
    async with init_devices():
        mg_kalpha_source = LabXraySourceReadable(LabXraySource.MG_KALPHA)
    return mg_kalpha_source


@pytest.fixture
async def mg_kalpha_source_signal_name(mg_kalpha_source: LabXraySourceReadable) -> str:
    return f"{mg_kalpha_source.name}-energy_ev"


async def test_source_energy_correct(
    al_kalpha_source: LabXraySourceReadable,
    mg_kalpha_source: LabXraySourceReadable,
):
    await assert_value(al_kalpha_source.energy_ev, float(LabXraySource.AL_KALPHA.value))
    await assert_value(mg_kalpha_source.energy_ev, float(LabXraySource.MG_KALPHA.value))


async def test_al_kalpha_read_describe(
    al_kalpha_source: LabXraySourceReadable,
    al_kalpha_source_signal_name: str,
):
    read_al = await al_kalpha_source.read()
    assert al_kalpha_source_signal_name in read_al
    assert read_al[al_kalpha_source_signal_name]["value"] == float(
        LabXraySource.AL_KALPHA.value
    )

    describe_al = await al_kalpha_source.describe()
    assert al_kalpha_source_signal_name in describe_al


async def test_mg_kalpha_read_describe(
    mg_kalpha_source: LabXraySourceReadable,
    mg_kalpha_source_signal_name: str,
):
    read_mg = await mg_kalpha_source.read()
    assert mg_kalpha_source_signal_name in read_mg
    assert read_mg[mg_kalpha_source_signal_name]["value"] == float(
        LabXraySource.MG_KALPHA.value
    )

    describe_mg = await mg_kalpha_source.describe()
    assert mg_kalpha_source_signal_name in describe_mg


def test_class_parents_definitions(
    al_kalpha_source: LabXraySourceReadable,
    mg_kalpha_source: LabXraySourceReadable,
):
    assert isinstance(al_kalpha_source, StandardReadable)
    assert isinstance(mg_kalpha_source, StandardReadable)
    assert not isinstance(al_kalpha_source, Movable)
    assert not isinstance(mg_kalpha_source, Movable)


def test_move_fail(
    al_kalpha_source: LabXraySourceReadable,
    mg_kalpha_source: LabXraySourceReadable,
    RE: RunEngine,
):
    new_energy = 100.0
    with pytest.raises(
        AssertionError, match=re.escape("does not implement all Movable methods")
    ):
        RE(mv(al_kalpha_source, new_energy))

    with pytest.raises(
        AssertionError, match=re.escape("does not implement all Movable methods")
    ):
        RE(mv(mg_kalpha_source, new_energy))


def test_move_energy_fail(
    al_kalpha_source: LabXraySourceReadable,
    mg_kalpha_source: LabXraySourceReadable,
    RE: RunEngine,
):
    new_energy = 100.0
    with pytest.raises(
        AssertionError, match=re.escape("does not implement all Movable methods")
    ):
        RE(mv(al_kalpha_source.energy_ev, new_energy))

    with pytest.raises(
        AssertionError, match=re.escape("does not implement all Movable methods")
    ):
        RE(mv(mg_kalpha_source.energy_ev, new_energy))
