import asyncio
import math

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import SignalR, StrictEnum
from ophyd_async.testing import assert_reading, get_mock_put, set_mock_value

from dodal.devices import b07, i09
from dodal.devices.electron_analyser import (
    to_kinetic_energy,
)
from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
)
from dodal.devices.electron_analyser.specs import (
    SpecsAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
)
from tests.devices.unit_tests.electron_analyser.util import (
    TEST_SEQUENCE_REGION_NAMES,
    assert_read_configuration_has_expected_value,
    create_analyser_device,
)


@pytest.fixture(
    params=[
        VGScientaAnalyserDriverIO[i09.LensMode, i09.PsuMode, i09.PassEnergy],
        SpecsAnalyserDriverIO[b07.LensMode, b07.PsuMode],
    ]
)
async def sim_driver(
    request: pytest.FixtureRequest, energy_sources: dict[str, SignalR[float]]
) -> AbstractAnalyserDriverIO:
    return await create_analyser_device(
        request.param,
        energy_sources,
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_modes_correctly(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region))

    get_mock_put(sim_driver.region_name).assert_called_once_with(region.name, wait=True)
    await assert_read_configuration_has_expected_value(
        sim_driver, "region_name", region.name
    )
    get_mock_put(sim_driver.energy_mode).assert_called_once_with(
        region.energy_mode, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "energy_mode", region.energy_mode
    )
    get_mock_put(sim_driver.acquisition_mode).assert_called_once_with(
        region.acquisition_mode, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "acquisition_mode", region.acquisition_mode
    )
    get_mock_put(sim_driver.lens_mode).assert_called_once_with(
        region.lens_mode, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "lens_mode", region.lens_mode
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_energy_values_correctly(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region))

    energy_source = sim_driver._get_energy_source(region.excitation_energy_source)
    excitation_energy = await energy_source.get_value()

    expected_low_e = to_kinetic_energy(
        region.low_energy, region.energy_mode, excitation_energy
    )
    expected_high_e = to_kinetic_energy(
        region.high_energy, region.energy_mode, excitation_energy
    )
    expected_pass_e = region.pass_energy

    expected_energy_source = energy_source.name

    get_mock_put(sim_driver.low_energy).assert_called_once_with(
        expected_low_e, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "low_energy", expected_low_e
    )
    get_mock_put(sim_driver.high_energy).assert_called_once_with(
        expected_high_e, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "high_energy", expected_high_e
    )
    get_mock_put(sim_driver.pass_energy).assert_called_once_with(
        expected_pass_e, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "pass_energy", expected_pass_e
    )

    get_mock_put(sim_driver.excitation_energy).assert_called_once_with(
        excitation_energy, wait=True
    )
    get_mock_put(sim_driver.excitation_energy_source).assert_called_once_with(
        expected_energy_source, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "excitation_energy_source", expected_energy_source
    )
    await assert_reading(
        sim_driver,
        {
            "sim_driver-excitation_energy": {"value": excitation_energy},
            "sim_driver-image": {"value": []},
            "sim_driver-spectrum": {"value": []},
            "sim_driver-total_intensity": {"value": 0.0},
        },
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_given_region_that_analyser_sets_channel_correctly(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region))

    expected_slices = region.slices
    expected_iterations = region.iterations
    get_mock_put(sim_driver.slices).assert_called_once_with(expected_slices, wait=True)
    await assert_read_configuration_has_expected_value(
        sim_driver, "slices", expected_slices
    )
    get_mock_put(sim_driver.iterations).assert_called_once_with(
        expected_iterations, wait=True
    )
    await assert_read_configuration_has_expected_value(
        sim_driver, "iterations", expected_iterations
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_that_data_to_read_is_correct(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region))

    expected_total_time = math.prod(
        await asyncio.gather(
            sim_driver.iterations.get_value(),
            sim_driver.total_steps.get_value(),
            sim_driver.step_time.get_value(),
        )
    )
    assert await sim_driver.total_time.get_value() == expected_total_time

    spectrum = np.array([1, 2, 3, 4, 5], dtype=float)
    expected_total_intensity = np.sum(spectrum)
    set_mock_value(sim_driver.spectrum, spectrum)
    assert await sim_driver.total_intensity.get_value() == expected_total_intensity


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
def test_analyser_correctly_selects_energy_source_from_region_input(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
) -> None:
    source_alias_name = region.excitation_energy_source
    energy_source = sim_driver._get_energy_source(source_alias_name)

    assert energy_source == sim_driver.energy_sources[source_alias_name]


def test_analyser_raise_error_on_invalid_energy_source_selected(
    sim_driver: AbstractAnalyserDriverIO,
) -> None:
    with pytest.raises(KeyError):
        sim_driver._get_energy_source("invalid_name")


def test_driver_throws_error_with_wrong_lens_mode(
    sim_driver: AbstractAnalyserDriverIO,
    RE: RunEngine,
) -> None:
    class LensModeTestEnum(StrictEnum):
        TEST_1 = "Invalid mode"

    lens_datatype = sim_driver.lens_mode.datatype
    lens_datatype_name = lens_datatype.__name__ if lens_datatype is not None else ""
    with pytest.raises(FailedStatus, match=f"is not a valid {lens_datatype_name}"):
        RE(bps.mv(sim_driver.lens_mode, LensModeTestEnum.TEST_1))


def test_driver_throws_error_with_wrong_acquisition_mode(
    sim_driver: AbstractAnalyserDriverIO,
    RE: RunEngine,
) -> None:
    class AcquisitionModeTestEnum(StrictEnum):
        TEST_1 = "Invalid mode"

    acq_datatype = sim_driver.acquisition_mode.datatype
    acq_datatype_name = acq_datatype.__name__ if acq_datatype is not None else ""
    with pytest.raises(FailedStatus, match=f"is not a valid {acq_datatype_name}"):
        RE(bps.mv(sim_driver.acquisition_mode, AcquisitionModeTestEnum.TEST_1))


def test_driver_throws_error_with_wrong_psu_mode(
    sim_driver: AbstractAnalyserDriverIO,
    RE: RunEngine,
) -> None:
    class PsuModeTestEnum(StrictEnum):
        TEST_1 = "Invalid mode"

    psu_datatype = sim_driver.psu_mode.datatype
    psu_datatype_name = psu_datatype.__name__ if psu_datatype is not None else ""
    with pytest.raises(FailedStatus, match=f"is not a valid {psu_datatype_name}"):
        RE(bps.mv(sim_driver.psu_mode, PsuModeTestEnum.TEST_1))
