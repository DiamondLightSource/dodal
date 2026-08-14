import asyncio

import pytest
from ophyd_async.core import NotConnectedError, SignalRW, init_devices, soft_signal_rw
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    assert_value,
    partial_reading,
)

from dodal.devices.selectable_source import (
    DualEnergySource,
    SelectedSource,
    get_obj_from_selected_source,
)


def test_get_obj_from_selected_source_get() -> None:
    obj1, obj2 = object(), object()
    selected_obj = get_obj_from_selected_source(SelectedSource.SOURCE1, obj1, obj2)
    assert selected_obj is obj1
    selected_obj = get_obj_from_selected_source(SelectedSource.SOURCE2, obj1, obj2)
    assert selected_obj is obj2


@pytest.fixture
def source_selector() -> SignalRW[SelectedSource]:
    with init_devices(mock=True):
        source_selector = soft_signal_rw(SelectedSource)
    return source_selector


@pytest.fixture
def source1() -> SignalRW[float]:
    with init_devices(mock=True):
        source1 = soft_signal_rw(float, initial_value=2200)
    return source1


@pytest.fixture
def source2() -> SignalRW[float]:
    with init_devices(mock=True):
        source2 = soft_signal_rw(float, initial_value=500)
    return source2


@pytest.fixture
async def dual_energy_source(
    source_selector: SignalRW[SelectedSource],
    source1: SignalRW[float],
    source2: SignalRW[float],
) -> DualEnergySource:
    with init_devices(mock=True):
        dual_energy_source = DualEnergySource(
            source1=source1,
            source2=source2,
            selected_source=source_selector,
        )
    return dual_energy_source


async def test_dual_energy_source_energy_is_correct_when_switching_between_sources(
    dual_energy_source: DualEnergySource,
    source_selector: SignalRW[SelectedSource],
    source1: SignalRW[float],
    source2: SignalRW[float],
) -> None:
    s1_val, s2_val = await asyncio.gather(source1.get_value(), source2.get_value())

    # Make sure energy sources values are different for this test so we can tell them a
    # part when switching
    assert s1_val != s2_val

    await source_selector.set(SelectedSource.SOURCE1)
    await assert_value(dual_energy_source.energy, s1_val)
    await source_selector.set(SelectedSource.SOURCE2)
    await assert_value(dual_energy_source.energy, s2_val)


async def test_dual_energy_souce_read(
    dual_energy_source: DualEnergySource,
    source_selector: SignalRW[SelectedSource],
    source1: SignalRW[float],
    source2: SignalRW[float],
) -> None:
    await source_selector.set(SelectedSource.SOURCE1)
    s1_val, s2_val = await asyncio.gather(source1.get_value(), source2.get_value())
    await assert_reading(
        dual_energy_source,
        {
            "source_selector": partial_reading(SelectedSource.SOURCE1),
            "dual_energy_source-energy": partial_reading(s1_val),
            "source1_name": partial_reading(s1_val),
            "source2_name": partial_reading(s2_val),
        },
    )


async def test_dual_energy_souce_read_configuration(
    dual_energy_source: DualEnergySource,
    source1: SignalRW[float],
    source2: SignalRW[float],
) -> None:
    await assert_configuration(
        dual_energy_source,
        {
            "dual_energy_source-source1": partial_reading(source1.name),
            "dual_energy_source-source2": partial_reading(source2.name),
        },
    )


def test_dual_energy_source_validate_config_signal(
    source_selector: SignalRW[SelectedSource],
) -> None:
    with init_devices(mock=True):
        source1 = soft_signal_rw(float)
        source2 = soft_signal_rw(float)
        with pytest.raises(
            NotConnectedError,
            match='Signal cannot have name "". Make sure the signal has been '
            "connected and named before passing to class DualEnergySource",
        ):
            DualEnergySource(
                source1=source1,
                source2=source2,
                selected_source=source_selector,
            )
