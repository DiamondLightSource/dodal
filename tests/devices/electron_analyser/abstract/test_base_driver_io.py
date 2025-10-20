from typing import get_origin
from unittest.mock import AsyncMock, patch

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import StrictEnum, init_devices
from ophyd_async.epics.adcore import ADImageMode
from ophyd_async.testing import get_mock_put

from dodal.devices import b07, i09
from dodal.devices.electron_analyser import DualEnergySource, EnergyMode, EnergySource
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
from dodal.testing.electron_analyser import create_driver
from tests.devices.electron_analyser.helper_util import (
    TEST_SEQUENCE_REGION_NAMES,
)


@pytest.fixture(
    params=[
        VGScientaAnalyserDriverIO[i09.LensMode, i09.PsuMode, i09.PassEnergy],
        SpecsAnalyserDriverIO[b07.LensMode, b07.PsuMode],
    ]
)
async def sim_driver(
    request: pytest.FixtureRequest,
    single_energy_source: EnergySource,
    dual_energy_source: DualEnergySource,
    RE: RunEngine,
) -> AbstractAnalyserDriverIO:
    source = single_energy_source
    if get_origin(request.param) is VGScientaAnalyserDriverIO:
        source = dual_energy_source
    async with init_devices(mock=True):
        sim_driver = await create_driver(
            request.param, prefix="TEST:", energy_source=source
        )
    return sim_driver


@pytest.mark.parametrize("region", TEST_SEQUENCE_REGION_NAMES, indirect=True)
async def test_driver_set(
    sim_driver: AbstractAnalyserDriverIO,
    region: AbstractBaseRegion,
    RE: RunEngine,
) -> None:
    sim_driver._set_region = AsyncMock()

    # Patch switch_energy_mode so we can check on calls, but still run the real function
    with patch.object(
        AbstractBaseRegion,
        "switch_energy_mode",
        side_effect=AbstractBaseRegion.switch_energy_mode,  # run the real method
        autospec=True,
    ) as mock_switch_energy_mode:
        RE(bps.mv(sim_driver, region))

        mock_switch_energy_mode.assert_called_once_with(
            region,
            EnergyMode.KINETIC,
            await sim_driver.energy_source.energy.get_value(),
        )

        if isinstance(sim_driver.energy_source, DualEnergySource):
            get_mock_put(
                sim_driver.energy_source.selected_source
            ).assert_called_once_with(region.excitation_energy_source, wait=True)

        # Check interal _set_region was set with ke_region
        ke_region = mock_switch_energy_mode.call_args[0][0].switch_energy_mode(
            EnergyMode.KINETIC,
            await sim_driver.energy_source.energy.get_value(),
        )
        sim_driver._set_region.assert_called_once_with(ke_region)

        get_mock_put(sim_driver.energy_mode).assert_called_once_with(
            region.energy_mode, wait=True
        )


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


@pytest.mark.asyncio
async def test_stage_sets_image_mode_and_calls_super(
    sim_driver: AbstractAnalyserDriverIO,
):
    # Patch image_mode.set and super().stage
    with patch.object(
        AbstractAnalyserDriverIO.__bases__[1], "stage", new=AsyncMock()
    ) as super_stage:
        sim_driver.image_mode.set = AsyncMock()
        await sim_driver.stage()
        sim_driver.image_mode.set.assert_awaited_once_with(ADImageMode.SINGLE)
        super_stage.assert_awaited_once()
