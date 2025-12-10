from unittest.mock import AsyncMock, patch

import pytest
from ophyd_async.core import TriggerInfo, get_mock_put, init_devices

from dodal.beamlines import b07, i09
from dodal.devices.electron_analyser.base import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    DualEnergySource,
    EnergySource,
)
from dodal.devices.electron_analyser.base.base_controller import (
    ElectronAnalyserController,
)
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
)
from dodal.testing.electron_analyser import create_driver
from tests.devices.electron_analyser.helper_util import (
    TEST_SEQUENCE_REGION_NAMES,
    get_test_sequence,
)


@pytest.fixture(
    params=[
        SpecsAnalyserDriverIO[b07.LensMode, b07.PsuMode],
        VGScientaAnalyserDriverIO[i09.LensMode, i09.PsuMode, i09.PassEnergy],
    ]
)
async def sim_driver(
    request: pytest.FixtureRequest,
) -> AbstractAnalyserDriverIO:
    async with init_devices(mock=True):
        sim_detector = create_driver(
            request.param,
            prefix="TEST:",
        )
    return sim_detector


@pytest.fixture
def sequence_file_path(
    sim_driver: AbstractAnalyserDriverIO,
) -> str:
    return get_test_sequence(type(sim_driver))


@pytest.fixture
def analyser_controller(
    sim_driver: AbstractAnalyserDriverIO,
    single_energy_source: EnergySource,
    dual_energy_source: DualEnergySource,
) -> ElectronAnalyserController[AbstractAnalyserDriverIO, AbstractBaseRegion]:
    if isinstance(sim_driver, SpecsAnalyserDriverIO):
        energy_source = single_energy_source
    elif isinstance(sim_driver, VGScientaAnalyserDriverIO):
        energy_source = dual_energy_source
    else:
        raise ValueError()

    return ElectronAnalyserController[AbstractAnalyserDriverIO, AbstractBaseRegion](
        sim_driver, energy_source, 0
    )


async def test_controller_prepare_sets_excitation_energy(
    analyser_controller: ElectronAnalyserController[
        AbstractAnalyserDriverIO, AbstractBaseRegion
    ],
) -> None:
    excitation_energy = await analyser_controller.energy_source.energy.get_value()
    await analyser_controller.prepare(TriggerInfo())
    get_mock_put(
        analyser_controller.driver.cached_excitation_energy
    ).assert_awaited_once_with(excitation_energy, wait=True)


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_controller_setup_with_region_sets_elected_source_and_converts_region_for_epics(
    analyser_controller: ElectronAnalyserController[
        AbstractAnalyserDriverIO, AbstractBaseRegion
    ],
    region: AbstractBaseRegion,
) -> None:
    energy_source = analyser_controller.energy_source

    sim_driver = analyser_controller.driver
    sim_driver.set = AsyncMock()

    # Patch switch_energy_mode so we can check on calls, but still run the real function
    with patch.object(
        AbstractBaseRegion,
        "prepare_for_epics",
        side_effect=AbstractBaseRegion.prepare_for_epics,  # run the real method
        autospec=True,
    ) as mock_prepare_for_epics:
        await analyser_controller.setup_with_region(region)

        mock_prepare_for_epics.assert_called_once_with(
            region,
            await energy_source.energy.get_value(),
        )

        if isinstance(energy_source, DualEnergySource):
            get_mock_put(energy_source.selected_source).assert_called_once_with(
                region.excitation_energy_source, wait=True
            )
        # Check set was called with epics_region
        epics_region = mock_prepare_for_epics.call_args[0][0].prepare_for_epics(
            await energy_source.energy.get_value(),
        )
        sim_driver.set.assert_called_once_with(epics_region)
