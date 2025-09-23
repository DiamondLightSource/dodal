from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    assert_value,
    partial_reading,
)

from dodal.devices.electron_analyser import (
    DualEnergySource,
    EnergySource,
    SelectedSource,
)
from dodal.devices.i09 import DCM
from dodal.devices.pgm import PGM


async def test_single_energy_source_read(
    single_energy_source: EnergySource,
    dcm: DCM,
) -> None:
    await assert_reading(
        single_energy_source,
        {
            f"{dcm.energy_in_ev.name}": partial_reading(
                await dcm.energy_in_ev.get_value()
            ),
        },
    )


async def test_single_energy_souce_read_configuration(
    single_energy_source: EnergySource,
    dcm: DCM,
) -> None:
    await assert_configuration(
        single_energy_source,
        {
            f"{single_energy_source.name}-wrapped_device_name": partial_reading(
                dcm.energy_in_ev.name
            ),
        },
    )


async def test_dual_energy_source_energy_is_correct_when_switching_between_sources(
    dual_energy_source: DualEnergySource,
    dcm: DCM,
    pgm: PGM,
) -> None:
    dcm_energy_val = await dcm.energy_in_ev.get_value()
    pgm_energy_val = await pgm.energy.user_readback.get_value()

    # Make sure energy sources values are different for this test so we can tell them a
    # part when switching
    assert dcm_energy_val != pgm_energy_val

    await dual_energy_source.selected_source.set(SelectedSource.SOURCE1)
    await assert_value(dual_energy_source.energy, dcm_energy_val)
    await dual_energy_source.selected_source.set(SelectedSource.SOURCE2)
    await assert_value(dual_energy_source.energy, pgm_energy_val)


async def test_dual_energy_souce_read(
    dual_energy_source: DualEnergySource,
    dcm: DCM,
    pgm: PGM,
) -> None:
    await dual_energy_source.selected_source.set(SelectedSource.SOURCE1)
    prefix = dual_energy_source.name
    await assert_reading(
        dual_energy_source,
        {
            f"{prefix}-selected_source": partial_reading(SelectedSource.SOURCE1),
            f"{dcm.energy_in_ev.name}": partial_reading(
                await dcm.energy_in_ev.get_value()
            ),
            f"{pgm.energy.user_readback.name}": partial_reading(
                await pgm.energy.user_readback.get_value()
            ),
        },
    )


async def test_dual_energy_souce_read_configuration(
    dual_energy_source: DualEnergySource,
    dcm: DCM,
    pgm: PGM,
) -> None:
    prefix = dual_energy_source.name
    await assert_configuration(
        dual_energy_source,
        {
            f"{prefix}-source1-wrapped_device_name": partial_reading(
                dcm.energy_in_ev.name
            ),
            f"{prefix}-source2-wrapped_device_name": partial_reading(
                pgm.energy.user_readback.name
            ),
        },
    )
