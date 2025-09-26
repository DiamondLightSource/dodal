from asyncio import wait_for
from contextlib import nullcontext
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp
from bluesky.run_engine import RunEngine
from ophyd.status import DeviceStatus, Status
from ophyd_async.core import init_devices
from ophyd_async.testing import get_mock_put, set_mock_value

from dodal.devices.fast_grid_scan import (
    FastGridScanCommon,
    GridScanParamsCommon,
    PandAFastGridScan,
    PandAGridScanParams,
    ZebraFastGridScanThreeD,
    ZebraGridScanParamsThreeD,
    set_fast_grid_scan_params,
)
from dodal.devices.i02_1.fast_grid_scan import ZebraFastGridScanTwoD
from dodal.devices.smargon import Smargon
from dodal.testing import patch_all_motors


def discard_status(st: Status | DeviceStatus):
    try:
        st.wait(0.01)
    except BaseException:
        pass


@pytest.fixture
async def zebra_fast_grid_scan():
    async with init_devices(mock=True):
        zebra_fast_grid_scan = ZebraFastGridScanThreeD(name="fake_FGS", prefix="FGS")

    return zebra_fast_grid_scan


@pytest.fixture
async def panda_fast_grid_scan():
    async with init_devices(mock=True):
        panda_fast_grid_scan = PandAFastGridScan(name="fake_PGS", prefix="PGS")

    return panda_fast_grid_scan


@pytest.fixture
async def zebra_fast_grid_scan_2d():
    async with init_devices(mock=True):
        fast_grid_scan = ZebraFastGridScanTwoD(prefix="", motion_controller_prefix="")
    return fast_grid_scan


@pytest.fixture
async def smargon():
    async with init_devices(mock=True):
        smargon = Smargon("")

    with patch_all_motors(smargon):
        yield smargon


@pytest.fixture(
    params=["zebra_fast_grid_scan", "panda_fast_grid_scan", "zebra_fast_grid_scan_2d"]
)
def grid_scan(request: pytest.FixtureRequest) -> FastGridScanCommon:
    instance = request.getfixturevalue(request.param)
    return instance


async def test_given_settings_valid_when_kickoff_then_run_started(
    grid_scan: FastGridScanCommon,
):
    set_mock_value(grid_scan.scan_invalid, False)
    set_mock_value(grid_scan.position_counter, 0)
    set_mock_value(grid_scan.status, 1)

    await grid_scan.kickoff()

    get_mock_put(grid_scan.run_cmd).assert_called_once()


async def test_waits_for_running_motion(grid_scan: FastGridScanCommon):
    set_mock_value(grid_scan.motion_program.running, 1)

    grid_scan.KICKOFF_TIMEOUT = 0.01

    with pytest.raises(TimeoutError):
        await grid_scan.kickoff()

    grid_scan.KICKOFF_TIMEOUT = 1

    set_mock_value(grid_scan.motion_program.running, 0)
    set_mock_value(grid_scan.status, 1)
    await grid_scan.kickoff()
    get_mock_put(grid_scan.run_cmd).assert_called_once()


@pytest.mark.parametrize(
    "steps, expected_images",
    [
        ((10, 10, 0), 100),
        ((30, 5, 10), 450),
        ((7, 0, 5), 35),
    ],
)
async def test_given_different_step_numbers_then_expected_images_correct(
    zebra_fast_grid_scan: ZebraFastGridScanThreeD, steps, expected_images
):
    set_mock_value(zebra_fast_grid_scan.x_steps, steps[0])
    set_mock_value(zebra_fast_grid_scan.y_steps, steps[1])
    set_mock_value(zebra_fast_grid_scan.z_steps, steps[2])

    RE = RunEngine(call_returns_result=True)

    result = RE(bps.rd(zebra_fast_grid_scan.expected_images))

    assert result.plan_result == expected_images  # type: ignore


@pytest.mark.parametrize(
    "steps, expected_images",
    [
        ((10, 10), 100),
        ((30, 5), 150),
        ((7, 0), 0),
    ],
)
async def test_given_different_2d_step_numbers_then_expected_images_correct(
    zebra_fast_grid_scan_2d: ZebraFastGridScanTwoD, steps, expected_images
):
    set_mock_value(zebra_fast_grid_scan_2d.x_steps, steps[0])
    set_mock_value(zebra_fast_grid_scan_2d.y_steps, steps[1])

    RE = RunEngine(call_returns_result=True)

    result = RE(bps.rd(zebra_fast_grid_scan_2d.expected_images))

    assert result.plan_result == expected_images  # type: ignore


@pytest.mark.parametrize(
    "use_pgs",
    [(False), (True)],
)
async def test_running_finished_with_all_images_done_then_complete_status_finishes_not_in_error(
    use_pgs,
    zebra_fast_grid_scan: ZebraFastGridScanThreeD,
    panda_fast_grid_scan: PandAFastGridScan,
    RE: RunEngine,
):
    grid_scan: ZebraFastGridScanThreeD | PandAFastGridScan = (
        panda_fast_grid_scan if use_pgs else zebra_fast_grid_scan
    )
    num_pos_1d = 2
    if use_pgs:
        RE(
            set_fast_grid_scan_params(
                grid_scan,
                PandAGridScanParams(
                    transmission_fraction=0.01, x_steps=num_pos_1d, y_steps=num_pos_1d
                ),
            )
        )
    else:
        RE(
            set_fast_grid_scan_params(
                grid_scan,
                ZebraGridScanParamsThreeD(
                    transmission_fraction=0.01, x_steps=num_pos_1d, y_steps=num_pos_1d
                ),
            )
        )
    set_mock_value(grid_scan.status, 1)

    complete_status = grid_scan.complete()
    assert not complete_status.done
    set_mock_value(grid_scan.position_counter, num_pos_1d**2)
    set_mock_value(grid_scan.status, 0)

    await wait_for(complete_status, 0.1)

    assert complete_status.done
    assert complete_status.exception() is None


@pytest.fixture
def motor_bundle_with_limits(smargon) -> Smargon:
    for axis in [
        smargon.x,
        smargon.y,
        smargon.z,
    ]:
        set_mock_value(axis.low_limit_travel, 0)
        set_mock_value(axis.high_limit_travel, 10)

    return smargon


@dataclass
class CompositeWithSmargon:
    smargon: Smargon


@pytest.fixture
def composite_with_smargon(motor_bundle_with_limits):
    return CompositeWithSmargon(motor_bundle_with_limits)


def check_parameter_validation(params, composite, expected_in_limits):
    if expected_in_limits:
        yield from params.validate_against_hardware(composite)
    else:
        with pytest.raises(ValueError):
            yield from params.validate_against_hardware(composite)


@pytest.fixture
def zebra_grid_scan_params():
    yield ZebraGridScanParamsThreeD(
        transmission_fraction=0.01,
        x_steps=10,
        y_steps=15,
        z_steps=20,
        x_step_size_mm=0.3,
        y_step_size_mm=0.2,
        z_step_size_mm=0.1,
        x_start_mm=0,
        y1_start_mm=1,
        y2_start_mm=2,
        z1_start_mm=3,
        z2_start_mm=4,
    )


@pytest.fixture
def panda_grid_scan_params():
    yield PandAGridScanParams(
        transmission_fraction=0.01,
        x_steps=10,
        y_steps=15,
        z_steps=20,
        x_step_size_mm=0.3,
        y_step_size_mm=0.2,
        z_step_size_mm=0.1,
        x_start_mm=0,
        y1_start_mm=1,
        y2_start_mm=2,
        z1_start_mm=3,
        z2_start_mm=4,
    )


@pytest.fixture(params=["zebra_grid_scan_params", "panda_grid_scan_params"])
def common_grid_scan_params(request: pytest.FixtureRequest):
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize(
    "grid_position, expected",
    [
        [np.array([-1, 2, 4]), pytest.raises(IndexError)],
        [np.array([11, 2, 4]), pytest.raises(IndexError)],
        [np.array([1, 17, 4]), pytest.raises(IndexError)],
        [np.array([1, 5, 22]), pytest.raises(IndexError)],
        [np.array([0, 0, 0]), nullcontext(np.array([0, 1, 4]))],
        [np.array([1, 1, 1]), nullcontext(np.array([0.3, 1.2, 4.1]))],
        [np.array([2, 11, 16]), nullcontext(np.array([0.6, 3.2, 5.6]))],
        [np.array([6, 5, 5]), nullcontext(np.array([1.8, 2.0, 4.5]))],
        [np.array([-0.51, 5, 5]), pytest.raises(IndexError)],
        [
            np.array([-0.5, 5, 5]),
            nullcontext(np.array([-0.5 * 0.3, 1 + 5 * 0.2, 4 + 5 * 0.1])),
        ],
        [np.array([5, -0.51, 5]), pytest.raises(IndexError)],
        [
            np.array([5, -0.5, 5]),
            nullcontext(np.array([5 * 0.3, 1 - 0.5 * 0.2, 4 + 5 * 0.1])),
        ],
        [np.array([5, 5, -0.51]), pytest.raises(IndexError)],
        [
            np.array([5, 5, -0.5]),
            nullcontext(np.array([5 * 0.3, 1 + 5 * 0.2, 4 - 0.5 * 0.1])),
        ],
        [np.array([9.51, 5, 5]), pytest.raises(IndexError)],
        [
            np.array([9.5, 5, 5]),
            nullcontext(np.array([9.5 * 0.3, 1 + 5 * 0.2, 4 + 5 * 0.1])),
        ],
        [np.array([5, 14.51, 5]), pytest.raises(IndexError)],
        [
            np.array([5, 14.5, 5]),
            nullcontext(np.array([5 * 0.3, 1 + 14.5 * 0.2, 4 + 5 * 0.1])),
        ],
        [np.array([5, 5, 19.51]), pytest.raises(IndexError)],
        [
            np.array([5, 5, 19.5]),
            nullcontext(np.array([5 * 0.3, 1 + 5 * 0.2, 4 + 19.5 * 0.1])),
        ],
    ],
)
def test_given_x_y_z_out_of_range_then_converting_to_motor_coords_raises(
    common_grid_scan_params: GridScanParamsCommon, grid_position, expected
):
    with expected as expected_value:
        motor_position = common_grid_scan_params.grid_position_to_motor_position(
            grid_position
        )
        assert np.allclose(motor_position, expected_value)


def test_can_run_fast_grid_scan_in_run_engine(
    grid_scan: FastGridScanCommon,
    zebra_fast_grid_scan: ZebraFastGridScanThreeD,
    panda_fast_grid_scan: PandAFastGridScan,
    RE: RunEngine,
):
    @bpp.run_decorator()
    def kickoff_and_complete(device: FastGridScanCommon):
        yield from bps.kickoff(device, group="kickoff")
        set_mock_value(device.status, 1)
        yield from bps.wait("kickoff")
        yield from bps.complete(device, group="complete")
        set_mock_value(device.status, 0)
        yield from bps.wait("complete")

    (RE(kickoff_and_complete(grid_scan)))
    assert RE.state == "idle"


@pytest.mark.parametrize(
    "test_dwell_times, expected_dwell_time_is_integer",
    [
        (9000, True),
        (1000, True),
        (100.1, True),
        (100.09, True),
        (150.7, False),
        (10, True),
        (99, True),
        (59, True),
        (0.4, False),
        (0.9, False),
        (0.44, False),
        (0.99, False),
        (0.01, False),
        (0.09, False),
        (0.001, False),
        (0.009, False),
    ],
)
def test_non_test_integer_dwell_time(test_dwell_times, expected_dwell_time_is_integer):
    if expected_dwell_time_is_integer:
        params = ZebraGridScanParamsThreeD(
            dwell_time_ms=test_dwell_times,
            transmission_fraction=0.01,
        )
        assert params.dwell_time_ms == test_dwell_times
    else:
        with pytest.raises(ValueError):
            ZebraGridScanParamsThreeD(
                dwell_time_ms=test_dwell_times,
                transmission_fraction=0.01,
            )


@patch("dodal.devices.fast_grid_scan.LOGGER.error")
async def test_timeout_on_complete_triggers_stop_and_logs_error(
    mock_log_error: MagicMock,
    zebra_fast_grid_scan: ZebraFastGridScanThreeD,
):
    zebra_fast_grid_scan.COMPLETE_STATUS = 0.01
    zebra_fast_grid_scan.stop_cmd = AsyncMock()
    set_mock_value(zebra_fast_grid_scan.status, 1)
    with pytest.raises(TimeoutError):
        await zebra_fast_grid_scan.complete()
    mock_log_error.assert_called_once()
    zebra_fast_grid_scan.stop_cmd.trigger.assert_awaited_once()


async def test_i02_1_gridscan_has_2d_behaviour(
    zebra_fast_grid_scan_2d: ZebraFastGridScanTwoD,
):
    three_d_movables = ["z_step_size_mm", "z2_start_mm", "y2_start_mm", "z_steps"]
    for movable in three_d_movables:
        assert movable not in zebra_fast_grid_scan_2d.movable_params.keys()
    set_mock_value(zebra_fast_grid_scan_2d.x_steps, 5)
    set_mock_value(zebra_fast_grid_scan_2d.y_steps, 4)
    assert await zebra_fast_grid_scan_2d.expected_images.get_value() == 20
