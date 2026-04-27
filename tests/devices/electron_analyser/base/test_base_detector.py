from collections.abc import Mapping
from unittest.mock import AsyncMock

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
)

from dodal.devices.electron_analyser.base import (
    GenericElectronAnalyserDetector,
    GenericSequence,
)
from tests.devices.electron_analyser.helper_util.sequence import get_test_sequence


@pytest.fixture
def sequence(sim_detector: GenericElectronAnalyserDetector) -> GenericSequence:
    return get_test_sequence(type(sim_detector))


def test_base_analyser_detector_trigger(
    sim_detector: GenericElectronAnalyserDetector,
    run_engine: RunEngine,
) -> None:
    sim_detector._controller.arm = AsyncMock()
    sim_detector._controller.wait_for_idle = AsyncMock()

    run_engine(bps.trigger(sim_detector, wait=True), wait=True)

    sim_detector._controller.arm.assert_awaited_once()
    sim_detector._controller.wait_for_idle.assert_awaited_once()


async def test_base_analyser_detector_read(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    driver_read = await sim_detector._controller.driver.read()
    await assert_reading(sim_detector, driver_read)


async def test_base_analyser_describe(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    energy_array = await sim_detector._controller.driver.energy_axis.get_value()
    angle_array = await sim_detector._controller.driver.angle_axis.get_value()
    data = await sim_detector.describe()
    assert data[f"{sim_detector._controller.driver.image.name}"]["shape"] == [
        len(angle_array),
        len(energy_array),
    ]


async def test_base_analyser_detector_configuration(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    driver_config = await sim_detector._controller.driver.read_configuration()
    await assert_configuration(sim_detector, driver_config)


async def test_base_analyser_detector_describe_configuration(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    driver_describe_config = (
        await sim_detector._controller.driver.describe_configuration()
    )

    assert await sim_detector.describe_configuration() == driver_describe_config


async def test_analyser_detector_stage(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    sim_detector._controller.disarm = AsyncMock()

    await sim_detector.stage()

    sim_detector._controller.disarm.assert_awaited_once()


async def test_analyser_detector_unstage(
    sim_detector: GenericElectronAnalyserDetector,
) -> None:
    sim_detector._controller.disarm = AsyncMock()

    await sim_detector.unstage()

    sim_detector._controller.disarm.assert_awaited_once()


def test_analyser_detector_trigger_called_controller_prepare(
    sim_detector: GenericElectronAnalyserDetector,
    run_engine: RunEngine,
) -> None:
    sim_detector._controller.prepare = AsyncMock()
    sim_detector._controller.arm = AsyncMock()
    sim_detector._controller.wait_for_idle = AsyncMock()

    run_engine(bps.trigger(sim_detector, wait=True), wait=True)

    sim_detector._controller.prepare.assert_awaited_once()
    sim_detector._controller.arm.assert_awaited_once()
    sim_detector._controller.wait_for_idle.assert_awaited_once()


def test_analyser_detector_set_called_controller_setup_with_region(
    sim_detector: GenericElectronAnalyserDetector,
    sequence: GenericSequence,
    run_engine: RunEngine,
) -> None:
    region = sequence.get_enabled_regions()[0]
    sim_detector._controller.setup_with_region = AsyncMock()
    run_engine(bps.mv(sim_detector, region), wait=True)
    sim_detector._controller.setup_with_region.assert_awaited_once_with(region)


def test_analyser_read_configuration_is_unique_per_region(
    sim_detector: GenericElectronAnalyserDetector,
    sequence: GenericSequence,
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
) -> None:

    def multi_region_analyser_plan(
        analyser: GenericElectronAnalyserDetector, seq: GenericSequence
    ):
        yield from bps.open_run()
        yield from bps.stage(analyser)
        yield from bps.prepare(analyser.sequence, seq)
        assert analyser.sequence.data is not None
        for region in analyser.sequence.data.get_enabled_regions():
            yield from bps.mv(analyser, region)
            yield from bps.trigger_and_read([analyser], name=region.name)
        yield from bps.unstage(analyser)
        yield from bps.close_run()

    run_engine(multi_region_analyser_plan(sim_detector, sequence))

    descriptor = run_engine_documents["descriptor"]
    drv = sim_detector._controller.driver

    # Test subset of data to check configuration of detector per region correctly renews
    # configutation cache and matches the region data it was given.
    for desc, region in zip(descriptor, sequence.get_enabled_regions(), strict=True):
        config_analyser_data = desc["configuration"][sim_detector.name]["data"]
        assert config_analyser_data[drv.region_name.name] == region.name
        assert config_analyser_data[drv.lens_mode.name] == region.lens_mode
        assert config_analyser_data[drv.pass_energy.name] == region.pass_energy
