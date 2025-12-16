import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import StrictEnum, init_devices

from dodal.devices import b07, i09
from dodal.devices.electron_analyser.base import GenericAnalyserDriverIO
from dodal.devices.electron_analyser.specs import (
    SpecsAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
)
from dodal.testing.electron_analyser import create_driver


@pytest.fixture(
    params=[
        VGScientaAnalyserDriverIO[i09.LensMode, i09.PsuMode, i09.PassEnergy],
        SpecsAnalyserDriverIO[b07.LensMode, b07.PsuMode],
    ]
)
async def sim_driver(
    request: pytest.FixtureRequest,
) -> GenericAnalyserDriverIO:
    async with init_devices(mock=True):
        sim_driver = create_driver(request.param, prefix="TEST:")
    return sim_driver


def test_driver_throws_error_with_wrong_lens_mode(
    sim_driver: GenericAnalyserDriverIO,
    run_engine: RunEngine,
) -> None:
    class LensModeTestEnum(StrictEnum):
        TEST_1 = "Invalid mode"

    lens_datatype = sim_driver.lens_mode.datatype
    lens_datatype_name = lens_datatype.__name__ if lens_datatype is not None else ""
    with pytest.raises(FailedStatus, match=f"is not a valid {lens_datatype_name}"):
        run_engine(bps.mv(sim_driver.lens_mode, LensModeTestEnum.TEST_1))


def test_driver_throws_error_with_wrong_acquisition_mode(
    sim_driver: GenericAnalyserDriverIO,
    run_engine: RunEngine,
) -> None:
    class AcquisitionModeTestEnum(StrictEnum):
        TEST_1 = "Invalid mode"

    acq_datatype = sim_driver.acquisition_mode.datatype
    acq_datatype_name = acq_datatype.__name__ if acq_datatype is not None else ""
    with pytest.raises(FailedStatus, match=f"is not a valid {acq_datatype_name}"):
        run_engine(bps.mv(sim_driver.acquisition_mode, AcquisitionModeTestEnum.TEST_1))


def test_driver_throws_error_with_wrong_psu_mode(
    sim_driver: GenericAnalyserDriverIO,
    run_engine: RunEngine,
) -> None:
    class PsuModeTestEnum(StrictEnum):
        TEST_1 = "Invalid mode"

    psu_datatype = sim_driver.psu_mode.datatype
    psu_datatype_name = psu_datatype.__name__ if psu_datatype is not None else ""
    with pytest.raises(FailedStatus, match=f"is not a valid {psu_datatype_name}"):
        run_engine(bps.mv(sim_driver.psu_mode, PsuModeTestEnum.TEST_1))
