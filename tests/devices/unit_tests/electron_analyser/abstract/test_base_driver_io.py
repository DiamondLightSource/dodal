import asyncio
import math

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import StrictEnum
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    get_mock_put,
    partial_reading,
    set_mock_value,
)

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
)


@pytest.fixture(
    params=[
        VGScientaAnalyserDriverIO[i09.LensMode],
        SpecsAnalyserDriverIO[b07.LensMode],
    ]
)
def driver_class(
    request: pytest.FixtureRequest,
) -> type[AbstractAnalyserDriverIO]:
    return request.param


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_sets_region_and_configuration_is_correct(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    RE: RunEngine,
) -> None:
    RE(bps.mv(sim_driver, region))

    get_mock_put(sim_driver.region_name).assert_called_once_with(region.name, wait=True)
    get_mock_put(sim_driver.energy_mode).assert_called_once_with(
        region.energy_mode, wait=True
    )
    get_mock_put(sim_driver.acquisition_mode).assert_called_once_with(
        region.acquisition_mode, wait=True
    )
    get_mock_put(sim_driver.lens_mode).assert_called_once_with(
        region.lens_mode, wait=True
    )

    energy_source = sim_driver._get_energy_source(region.excitation_energy_source)
    excitation_energy = await energy_source.get_value()

    expected_low_e = to_kinetic_energy(
        region.low_energy, region.energy_mode, excitation_energy
    )
    expected_high_e = to_kinetic_energy(
        region.high_energy, region.energy_mode, excitation_energy
    )
    expected_pass_e_type = sim_driver.pass_energy_type
    expected_pass_e = expected_pass_e_type(region.pass_energy)

    get_mock_put(sim_driver.low_energy).assert_called_once_with(
        expected_low_e, wait=True
    )
    get_mock_put(sim_driver.high_energy).assert_called_once_with(
        expected_high_e, wait=True
    )
    get_mock_put(sim_driver.pass_energy).assert_called_once_with(
        expected_pass_e, wait=True
    )
    get_mock_put(sim_driver.excitation_energy).assert_called_once_with(
        excitation_energy, wait=True
    )
    get_mock_put(sim_driver.excitation_energy_source).assert_called_once_with(
        energy_source.name, wait=True
    )
    get_mock_put(sim_driver.slices).assert_called_once_with(region.slices, wait=True)
    get_mock_put(sim_driver.iterations).assert_called_once_with(
        region.iterations, wait=True
    )
    mock_values = 10
    set_mock_value(sim_driver.total_steps, mock_values)
    set_mock_value(sim_driver.step_time, mock_values)

    expected_total_time = math.prod(
        await asyncio.gather(
            sim_driver.iterations.get_value(),
            sim_driver.total_steps.get_value(),
            sim_driver.step_time.get_value(),
        )
    )

    # Depends on implementation, so get directly from device.
    energy_axis = await sim_driver.energy_axis.get_value()
    binding_axis = await sim_driver.binding_energy_axis.get_value()
    angle_axis = await sim_driver.angle_axis.get_value()

    prefix = sim_driver.name + "-"

    # Check partial match as different analysers will have more fields
    await assert_configuration(
        sim_driver,
        {
            f"{prefix}region_name": partial_reading(region.name),
            f"{prefix}energy_mode": partial_reading(region.energy_mode),
            f"{prefix}acquisition_mode": partial_reading(region.acquisition_mode),
            f"{prefix}lens_mode": partial_reading(region.lens_mode),
            f"{prefix}low_energy": partial_reading(expected_low_e),
            f"{prefix}high_energy": partial_reading(expected_high_e),
            f"{prefix}pass_energy": partial_reading(expected_pass_e),
            f"{prefix}excitation_energy_source": partial_reading(energy_source.name),
            f"{prefix}slices": partial_reading(region.slices),
            f"{prefix}iterations": partial_reading(region.iterations),
            f"{prefix}total_steps": partial_reading(mock_values),
            f"{prefix}step_time": partial_reading(mock_values),
            f"{prefix}total_time": partial_reading(expected_total_time),
            f"{prefix}energy_axis": partial_reading(energy_axis),
            f"{prefix}binding_energy_axis": partial_reading(binding_axis),
            f"{prefix}angle_axis": partial_reading(angle_axis),
        },
        full_match=False,
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_analyser_reading_is_correct(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    RE: RunEngine,
) -> None:
    energy_source = sim_driver._get_energy_source(region.excitation_energy_source)
    excitation_energy = await energy_source.get_value()

    spectrum = np.array([1, 2, 3, 4, 5], dtype=float)
    expected_total_intensity = np.sum(spectrum)
    set_mock_value(sim_driver.spectrum, spectrum)

    prefix = sim_driver.name + "-"
    await assert_reading(
        sim_driver,
        {
            f"{prefix}excitation_energy": partial_reading(excitation_energy),
            f"{prefix}image": partial_reading([]),
            f"{prefix}spectrum": partial_reading(spectrum),
            f"{prefix}total_intensity": partial_reading(expected_total_intensity),
        },
        full_match=True,
    )


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


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
def test_driver_throws_error_with_wrong_typed_modes(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    RE: RunEngine,
) -> None:
    class TestEnum(StrictEnum):
        TEST_1 = "Invalid mode"

    region.lens_mode = TestEnum.TEST_1
    region.acquisition_mode = TestEnum.TEST_1

    acq_datatype = sim_driver.acquisition_mode.datatype
    acq_datatype_name = acq_datatype.__name__ if acq_datatype is not None else ""

    with pytest.raises(FailedStatus, match=f"is not a valid {acq_datatype_name}"):
        RE(bps.mv(sim_driver.acquisition_mode, region.acquisition_mode))

    lens_datatype = sim_driver.lens_mode.datatype
    lens_datatype_name = lens_datatype.__name__ if lens_datatype is not None else ""
    with pytest.raises(FailedStatus, match=f"is not a valid {lens_datatype_name}"):
        RE(bps.mv(sim_driver.lens_mode, region.lens_mode))
