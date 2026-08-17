from math import ceil

import pytest
from ophyd_async.core import (
    DetectorTrigger,
    EnableDisable,
    PathProvider,
    TriggerInfo,
    init_devices,
    set_mock_value,
)

from dodal.devices.tetramm.summing_tetramm import (
    SummingTetrammDetector,
    SummingTetrammTriggerLogic,
)

from .conftest import configure_tetramm


@pytest.fixture
async def summing_tetramm(
    static_path_provider: PathProvider,
) -> SummingTetrammDetector:
    async with init_devices(mock=True):
        tetramm = SummingTetrammDetector(
            "MY-TETRAMM:",
            static_path_provider,
        )
    configure_tetramm(tetramm)

    return tetramm


VALID_TEST_TOTAL_TRIGGERS = 5
VALID_TEST_EXPOSURE_TIME_PER_COLLECTION = 1 / 6
VALID_TEST_EXPOSURE_TIME = (
    VALID_TEST_EXPOSURE_TIME_PER_COLLECTION / VALID_TEST_TOTAL_TRIGGERS
)
VALID_TEST_DEADTIME = 1 / 100


async def test_has_extra_plugins(summing_tetramm: SummingTetrammDetector):
    assert hasattr(summing_tetramm, "stats")
    assert hasattr(summing_tetramm, "proc1")
    assert hasattr(summing_tetramm, "roi")


async def test_describe_uses_summing_shape(
    summing_tetramm: SummingTetrammDetector,
    static_path_provider: PathProvider,
):
    """SummingTetrammDetector overrides get_shape() to return a single dimension of
    size 1, collapsing the [num_channels, to_average] shape of the base device.
    """
    trigger_info = TriggerInfo(
        number_of_events=1,
        trigger=DetectorTrigger.EXTERNAL_EDGE,
        deadtime=1e-4,
        livetime=1,
        exposure_timeout=0.001,
    )

    await summing_tetramm.stage()
    await summing_tetramm.prepare(trigger_info)

    path_info = static_path_provider(summing_tetramm.name)
    expected_path = (
        path_info.directory_path.joinpath(path_info.filename + ".h5")
        .as_uri()
        .replace("file:///", "file://localhost/")
    )

    assert await summing_tetramm.describe() == {
        "tetramm": {
            "source": expected_path,
            "shape": [1, 1],
            "dtype_numpy": "<f8",
            "dtype": "number",
            "external": "STREAM:",
        }
    }


async def test_prepare_connects_plugin_ports(
    summing_tetramm: SummingTetrammDetector,
):
    """prepare() wires the plugin chain: file_io ← proc1 ← roi ← stats."""
    await summing_tetramm.prepare(
        TriggerInfo(
            number_of_events=1,
            trigger=DetectorTrigger.EXTERNAL_EDGE,
            deadtime=VALID_TEST_DEADTIME,
            livetime=VALID_TEST_EXPOSURE_TIME,
        )
    )

    stats_port = await summing_tetramm.stats.port_name.get_value()
    roi_port = await summing_tetramm.roi.port_name.get_value()
    proc1_port = await summing_tetramm.proc1.port_name.get_value()

    assert (await summing_tetramm.roi.nd_array_port.get_value()) == stats_port
    assert (await summing_tetramm.proc1.nd_array_port.get_value()) == roi_port
    assert (await summing_tetramm.file_io.nd_array_port.get_value()) == proc1_port


async def test_prepare_sets_roi_and_proc_parameters(
    summing_tetramm: SummingTetrammDetector,
):
    to_average = 3
    set_mock_value(summing_tetramm.driver.to_average, to_average)

    await summing_tetramm.prepare(
        TriggerInfo(
            number_of_events=1,
            trigger=DetectorTrigger.EXTERNAL_EDGE,
            deadtime=VALID_TEST_DEADTIME,
            livetime=5,
        )
    )

    assert (await summing_tetramm.roi.size_x.get_value()) == to_average
    assert (await summing_tetramm.roi.bin_x.get_value()) == to_average
    assert (await summing_tetramm.driver.values_per_reading.get_value()) == 50
    assert (await summing_tetramm.proc1.scale.get_value()) == 50
    assert (
        await summing_tetramm.proc1.enable_scale.get_value()
    ) == EnableDisable.ENABLE


@pytest.mark.parametrize(
    "exposure, expected_values_per_reading",
    [
        # Small exposure: ceil(10 * exposure) < minimum_samples=5, so clamped to 5
        (0.01, 5),
        # Large exposure: ceil(10 * 2.0) = 20 > minimum_samples=5
        (2.0, ceil(10 * 2.0)),
        # Boundary: exactly at minimum (ceil(10 * 0.5) = 5 == minimum_samples)
        (0.5, ceil(10 * 0.5)),
    ],
)
async def test_set_exposure_sets_values_per_reading(
    summing_tetramm: SummingTetrammDetector,
    exposure: float,
    expected_values_per_reading: int,
):
    """TetrammTriggerLogic.set_exposure sets values_per_reading to
    max(minimum_samples, ceil(10 * exposure)), unlike the base class which does not
    set values_per_reading at all.
    """
    trigger_logic = SummingTetrammTriggerLogic(
        summing_tetramm.driver, summing_tetramm.file_io
    )
    await trigger_logic.set_values_per_reading(exposure)

    assert (
        await summing_tetramm.driver.values_per_reading.get_value()
    ) == expected_values_per_reading
