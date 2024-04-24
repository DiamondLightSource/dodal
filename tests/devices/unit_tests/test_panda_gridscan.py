import pytest
from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp
from bluesky.run_engine import RunEngine
from mockito import mock, verify, when
from mockito.matchers import ANY
from ophyd.sim import instantiate_fake_device, make_fake_device

from dodal.devices.panda_fast_grid_scan import (
    PandAFastGridScan,
    PandAGridScanParams,
    set_fast_grid_scan_params,
)
from dodal.devices.smargon import Smargon


@pytest.fixture
def fast_grid_scan(request):
    fast_grid_scan: PandAFastGridScan = instantiate_fake_device(
        PandAFastGridScan, name=f"test fake FGS: {request.node.name}"
    )
    fast_grid_scan.scan_invalid.pvname = ""

    yield fast_grid_scan


def test_given_settings_valid_when_kickoff_then_run_started(
    fast_grid_scan: PandAFastGridScan,
):
    when(fast_grid_scan.scan_invalid).get().thenReturn(False)
    when(fast_grid_scan.position_counter).get().thenReturn(0)

    mock_run_set_status = mock()
    when(fast_grid_scan.run_cmd).put(ANY).thenReturn(mock_run_set_status)
    fast_grid_scan.status.subscribe = lambda func, **_: func(1)

    status = fast_grid_scan.kickoff()

    status.wait()
    assert status.exception() is None

    verify(fast_grid_scan.run_cmd).put(1)


@pytest.mark.parametrize(
    "steps, expected_images",
    [
        ((10, 10, 0), 100),
        ((30, 5, 10), 450),
        ((7, 0, 5), 35),
    ],
)
def test_given_different_step_numbers_then_expected_images_correct(
    fast_grid_scan: PandAFastGridScan, steps, expected_images
):
    fast_grid_scan.x_steps.sim_put(steps[0])  # type: ignore
    fast_grid_scan.y_steps.sim_put(steps[1])  # type: ignore
    fast_grid_scan.z_steps.sim_put(steps[2])  # type: ignore

    assert fast_grid_scan.expected_images.get() == expected_images


def test_running_finished_with_all_images_done_then_complete_status_finishes_not_in_error(
    fast_grid_scan: PandAFastGridScan, RE: RunEngine
):
    num_pos_1d = 2
    RE(
        set_fast_grid_scan_params(
            fast_grid_scan,
            PandAGridScanParams(
                x_steps=num_pos_1d,
                y_steps=num_pos_1d,
                transmission_fraction=0.01,
            ),
        )
    )

    fast_grid_scan.status.sim_put(1)  # type: ignore

    complete_status = fast_grid_scan.complete()
    assert not complete_status.done
    fast_grid_scan.position_counter.sim_put(num_pos_1d**2)  # type: ignore
    fast_grid_scan.status.sim_put(0)  # type: ignore

    complete_status.wait()

    assert complete_status.done
    assert complete_status.exception() is None


def create_motor_bundle_with_limits(low_limit, high_limit) -> Smargon:
    FakeSmargon = make_fake_device(Smargon)
    grid_scan_motor_bundle: Smargon = FakeSmargon(name="test fake Smargon")
    grid_scan_motor_bundle.wait_for_connection()
    for axis in [
        grid_scan_motor_bundle.x,
        grid_scan_motor_bundle.y,
        grid_scan_motor_bundle.z,
    ]:
        axis.low_limit_travel.sim_put(low_limit)  # type: ignore
        axis.high_limit_travel.sim_put(high_limit)  # type: ignore
    return grid_scan_motor_bundle


def test_can_run_fast_grid_scan_in_run_engine(fast_grid_scan, RE: RunEngine):
    @bpp.run_decorator()
    def kickoff_and_complete(device):
        yield from bps.kickoff(device)
        yield from bps.complete(device)

    RE(kickoff_and_complete(fast_grid_scan))
    assert RE.state == "idle"
