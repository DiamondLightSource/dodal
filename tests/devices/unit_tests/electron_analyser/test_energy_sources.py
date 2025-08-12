from ophyd_async.core import SignalR
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    assert_value,
    partial_reading,
)

from dodal.devices.electron_analyser import (
    DualEnergySource,
    SelectedSource,
    SingleEnergySource,
)


async def test_single_energy_source_read(
    single_energy_source: SingleEnergySource, dcm_energy: SignalR[float]
) -> None:
    await assert_reading(
        single_energy_source,
        {
            f"{single_energy_source.name}-excitation_energy": partial_reading(
                await dcm_energy.get_value()
            ),
        },
    )


async def test_single_energy_souce_read_configuration(
    single_energy_source: DualEnergySource,
    dcm_energy: SignalR[float],
) -> None:
    await assert_configuration(
        single_energy_source,
        {
            f"{single_energy_source.name}-source_device": partial_reading(
                dcm_energy.name
            ),
        },
    )


async def test_dual_energy_source_energy_is_correct_when_switching_between_sources(
    dual_energy_source: DualEnergySource,
    dcm_energy: SignalR[float],
    pgm_energy: SignalR[float],
) -> None:
    dcm_energy_val = await dcm_energy.get_value()
    pgm_energy_val = await pgm_energy.get_value()

    # Make sure energy sources values are different for this test so we can tell them a
    # part when switching
    assert dcm_energy_val != pgm_energy_val

    await dual_energy_source.selected_source.set(SelectedSource.SOURCE1)
    await assert_value(dual_energy_source.excitation_energy, dcm_energy_val)
    await dual_energy_source.selected_source.set(SelectedSource.SOURCE2)
    await assert_value(dual_energy_source.excitation_energy, pgm_energy_val)


async def test_dual_energy_souce_read(
    dual_energy_source: DualEnergySource,
    dcm_energy: SignalR[float],
    pgm_energy: SignalR[float],
) -> None:
    await dual_energy_source.selected_source.set(SelectedSource.SOURCE1)
    prefix = dual_energy_source.name
    await assert_reading(
        dual_energy_source,
        {
            f"{prefix}-selected_source": partial_reading(SelectedSource.SOURCE1),
            f"{prefix}-excitation_energy": partial_reading(
                await dcm_energy.get_value()
            ),
        },
    )

    await dual_energy_source.selected_source.set(SelectedSource.SOURCE2)
    await assert_reading(
        dual_energy_source,
        {
            f"{prefix}-selected_source": partial_reading(SelectedSource.SOURCE2),
            f"{prefix}-excitation_energy": partial_reading(
                await pgm_energy.get_value()
            ),
        },
    )


async def test_dual_energy_souce_read_configuration(
    dual_energy_source: DualEnergySource,
    dcm_energy: SignalR[float],
    pgm_energy: SignalR[float],
) -> None:
    prefix = dual_energy_source.name
    await assert_configuration(
        dual_energy_source,
        {
            f"{prefix}-source1_device": partial_reading(dcm_energy.name),
            f"{prefix}-source2_device": partial_reading(pgm_energy.name),
        },
    )
