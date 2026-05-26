from collections.abc import Mapping
from unittest.mock import AsyncMock

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.testing import assert_value

from dodal.devices.electron_analyser.base import (
    EnergyMode,
    GenericElectronAnalyserDetector,
    GenericRegion,
    GenericSequence,
)
from tests.devices.electron_analyser.helper_util import (
    generate_fixture_regions_pair,
    load_b07_specs_test_seq,
    load_i09_vgscienta_test_seq,
)

DETECTOR_REGIONS_PAIR = [
    *generate_fixture_regions_pair("ew4000", load_i09_vgscienta_test_seq().regions),
    *generate_fixture_regions_pair("b07b_specs150", load_b07_specs_test_seq().regions),
]


@pytest.mark.parametrize(
    ("sim_detector", "region"), DETECTOR_REGIONS_PAIR, indirect=["sim_detector"]
)
async def test_base_analyser_detector_describe_configuration(
    sim_detector: GenericElectronAnalyserDetector, region: GenericRegion
) -> None:
    await sim_detector.set(region)
    driver = sim_detector._region_logic.driver

    # Check binding energy is correct
    is_region_binding = region.is_binding_energy()
    is_driver_binding = await driver.energy_mode.get_value() == EnergyMode.BINDING
    # Catch that driver correctly reflects what region energy mode is.
    assert is_region_binding == is_driver_binding
    energy_axis = await driver.energy_axis.get_value()
    excitation_energy = (
        await sim_detector._region_logic.energy_source.energy.get_value()
    )
    expected_binding_energy_axis = np.array(
        [excitation_energy - e if is_driver_binding else e for e in energy_axis]
    )
    await assert_value(sim_detector.binding_energy_axis, expected_binding_energy_axis)


async def test_analyser_detector_stage(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    sim_detector.sequence.stage = AsyncMock()
    await sim_detector.stage()
    sim_detector.sequence.stage.assert_awaited_once()


async def test_analyser_detector_unstage(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    sim_detector.sequence.unstage = AsyncMock()
    await sim_detector.unstage()
    sim_detector.sequence.unstage.assert_awaited_once()


@pytest.mark.parametrize(
    ("sim_detector", "region"), DETECTOR_REGIONS_PAIR, indirect=["sim_detector"]
)
def test_analyser_detector_set_called_region_logic_setup_with_region(
    sim_detector: GenericElectronAnalyserDetector,
    region: GenericRegion,
    run_engine: RunEngine,
) -> None:
    sim_detector._region_logic.setup_with_region = AsyncMock()
    run_engine(bps.mv(sim_detector, region), wait=True)
    sim_detector._region_logic.setup_with_region.assert_awaited_once_with(region)


@pytest.mark.parametrize(
    ("sim_detector", "sequence"),
    [
        pytest.param("ew4000", load_i09_vgscienta_test_seq()),
        pytest.param("b07b_specs150", load_b07_specs_test_seq()),
    ],
    indirect=["sim_detector"],
)
def test_analyser_read_configuration_is_unique_per_region(
    sim_detector: GenericElectronAnalyserDetector,
    sequence: GenericSequence,
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
) -> None:

    def multi_region_analyser_plan(
        analyser: GenericElectronAnalyserDetector, seq: GenericSequence
    ):
        yield from bps.prepare(analyser.sequence, seq)
        yield from bps.open_run()
        yield from bps.stage(analyser)
        assert analyser.sequence.data is not None
        for region in analyser.sequence.data.get_enabled_regions():
            yield from bps.mv(analyser, region)
            yield from bps.trigger_and_read([analyser], name=region.name)
        yield from bps.unstage(analyser)
        yield from bps.close_run()

    run_engine(multi_region_analyser_plan(sim_detector, sequence))

    descriptor = run_engine_documents["descriptor"]
    drv = sim_detector._region_logic.driver

    # Test subset of data to check configuration of detector per region correctly renews
    # configutation cache and matches the region data it was given.
    for desc, region in zip(descriptor, sequence.get_enabled_regions(), strict=True):
        config_analyser_data = desc["configuration"][sim_detector.name]["data"]
        assert config_analyser_data[drv.region_name.name] == region.name
        assert config_analyser_data[drv.lens_mode.name] == region.lens_mode
        assert config_analyser_data[drv.pass_energy.name] == region.pass_energy
