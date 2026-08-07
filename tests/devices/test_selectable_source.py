import asyncio

import pytest
from ophyd_async.core import NotConnectedError, SignalRW, init_devices, soft_signal_rw
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    assert_value,
    partial_reading,
)

from dodal.devices.beamlines.i09 import Grating
from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorWithDSpacing,
    PitchAndRollCrystal,
    StationaryCrystal,
)
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.selectable_source import (
    DualEnergySource,
    SelectedSource,
    get_obj_from_selected_source,
)


def test_get_obj_from_selected_source_get() -> None:
    obj1, obj2 = 1, 2
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
async def dual_energy_source(
    source_selector: SignalRW[SelectedSource],
) -> DualEnergySource:
    with init_devices(mock=True):
        dcm = DoubleCrystalMonochromatorWithDSpacing(
            "DCM:", PitchAndRollCrystal, StationaryCrystal
        )
        pgm = PlaneGratingMonochromator("PGM:", Grating)
    # Do in new context so that dcm and pgm are connected and named before giving to
    # dual_energy_source.
    with init_devices(mock=True):
        dual_energy_source = DualEnergySource(
            source1=dcm.energy_in_eV,
            source2=pgm.energy.user_readback,
            selected_source=source_selector,
        )
    await asyncio.gather(dcm.energy_in_keV.set(2.2), pgm.energy.set(500))
    return dual_energy_source


async def test_dual_energy_source_energy_is_correct_when_switching_between_sources(
    dual_energy_source: DualEnergySource,
) -> None:
    dcm_energy_val = await dual_energy_source.source1_ref().get_value()
    pgm_energy_val = await dual_energy_source.source2_ref().get_value()

    # Make sure energy sources values are different for this test so we can tell them a
    # part when switching
    assert dcm_energy_val != pgm_energy_val

    await dual_energy_source.selected_source_ref().set(SelectedSource.SOURCE1)
    await assert_value(dual_energy_source.energy, dcm_energy_val)
    await dual_energy_source.selected_source_ref().set(SelectedSource.SOURCE2)
    await assert_value(dual_energy_source.energy, pgm_energy_val)


async def test_dual_energy_souce_read(dual_energy_source: DualEnergySource) -> None:
    await dual_energy_source.selected_source_ref().set(SelectedSource.SOURCE1)

    source1_energy_value = await dual_energy_source.source1_ref().get_value()
    source2_energy_value = await dual_energy_source.source2_ref().get_value()

    await assert_reading(
        dual_energy_source,
        {
            "source_selector": partial_reading(SelectedSource.SOURCE1),
            "dual_energy_source-energy": partial_reading(source1_energy_value),
            "dcm-energy_in_eV": partial_reading(source1_energy_value),
            "pgm-energy": partial_reading(source2_energy_value),
        },
    )


async def test_dual_energy_souce_read_configuration(
    dual_energy_source: DualEnergySource,
) -> None:
    prefix = dual_energy_source.name
    await assert_configuration(
        dual_energy_source,
        {
            f"{prefix}-source1": partial_reading(dual_energy_source.source1_ref().name),
            f"{prefix}-source2": partial_reading(dual_energy_source.source2_ref().name),
        },
    )


def test_dual_energy_source_validate_config_signal(
    source_selector: SignalRW[SelectedSource],
) -> None:
    with init_devices(mock=True):
        dcm = DoubleCrystalMonochromatorWithDSpacing(
            "DCM:", PitchAndRollCrystal, StationaryCrystal
        )
        pgm = PlaneGratingMonochromator("PGM:", Grating)
        with pytest.raises(
            NotConnectedError,
            match='Signal cannot have name "". Make sure the signal has been '
            "connected and named before passing to class DualEnergySource",
        ):
            DualEnergySource(
                source1=dcm.energy_in_eV,
                source2=pgm.energy.user_readback,
                selected_source=source_selector,
            )
