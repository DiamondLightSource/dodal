from typing import Any

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import SignalR, StrictEnum
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    get_mock_put,
)

from dodal.devices import b07, i09
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
from tests.devices.unit_tests.electron_analyser.helpers import (
    TEST_SEQUENCE_REGION_NAMES,
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
async def test_abstract_analyser_sets_region_and_configuration_is_correct(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    expected_abstract_driver_config_reading: dict[str, dict[str, Any]],
    RE: RunEngine,
) -> None:
    expected_config = expected_abstract_driver_config_reading
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

    prefix = sim_driver.name + "-"
    VAL = "value"
    expected_low_e = expected_config[prefix + "low_energy"][VAL]
    expected_high_e = expected_config[prefix + "high_energy"][VAL]
    expected_pass_e = expected_config[prefix + "pass_energy"][VAL]
    expected_excitation_e_source = expected_config[prefix + "excitation_energy_source"][
        VAL
    ]

    get_mock_put(sim_driver.low_energy).assert_called_once_with(
        expected_low_e, wait=True
    )
    get_mock_put(sim_driver.high_energy).assert_called_once_with(
        expected_high_e, wait=True
    )
    get_mock_put(sim_driver.pass_energy).assert_called_once_with(
        expected_pass_e, wait=True
    )
    get_mock_put(sim_driver.excitation_energy_source).assert_called_once_with(
        expected_excitation_e_source, wait=True
    )
    get_mock_put(sim_driver.slices).assert_called_once_with(region.slices, wait=True)
    get_mock_put(sim_driver.iterations).assert_called_once_with(
        region.iterations, wait=True
    )

    # Check partial match as different analysers will have more fields
    await assert_configuration(
        sim_driver,
        expected_abstract_driver_config_reading,
        full_match=False,
    )


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_abstract_analyser_sets_region_and_reading_is_correct(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    expected_abstract_driver_describe_reading,
    RE: RunEngine,
) -> None:
    energy_source = sim_driver._get_energy_source(region.excitation_energy_source)
    excitation_energy = await energy_source.get_value()

    get_mock_put(sim_driver.excitation_energy).assert_called_once_with(
        excitation_energy, wait=True
    )

    await assert_reading(
        sim_driver,
        expected_abstract_driver_describe_reading,
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
