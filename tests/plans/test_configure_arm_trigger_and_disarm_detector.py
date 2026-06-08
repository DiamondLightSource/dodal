from unittest.mock import MagicMock

import pytest
from bluesky.run_engine import RunEngine
from daq_config_server import ConfigClient
from ophyd_async.core import (
    DetectorTrigger,
    TriggerInfo,
    callback_on_mock_put,
    get_mock,
    set_mock_value,
)
from ophyd_async.fastcs.eiger import EigerDetector as FastEiger

from dodal.common.beamlines.beamline_utils import set_config_client
from dodal.devices.detector import DetectorParams
from dodal.plans.configure_arm_trigger_and_disarm_detector import (
    configure_arm_trigger_and_disarm_detector,
)


@pytest.fixture
async def fake_eiger() -> FastEiger:
    fake_eiger = FastEiger("", MagicMock())
    await fake_eiger.connect(mock=True)
    set_mock_value(fake_eiger.detector.bit_depth_image, 32)
    return fake_eiger


async def test_configure_arm_trigger_and_disarm_detector(
    fake_eiger: FastEiger, eiger_params: DetectorParams, run_engine: RunEngine
):
    set_config_client(ConfigClient("test"))
    trigger_info = TriggerInfo(
        # Manual trigger, so setting number of triggers to 1.
        number_of_events=1,
        trigger=DetectorTrigger.INTERNAL,
        deadtime=0.0001,
    )

    filename: str = "filename.h5"

    def set_detector_into_writing_state(*args, **kwargs) -> None:
        # Mimics capturing and immediete completion status on Eiger.
        set_mock_value(fake_eiger.od.writing, True)
        set_mock_value(fake_eiger.od.file_prefix, filename)
        set_mock_value(fake_eiger.od.acquisition_id, filename)
        set_mock_value(fake_eiger.detector.state, "idle")

    callback_on_mock_put(
        fake_eiger.od.fp.start_writing, set_detector_into_writing_state
    )

    # Mimics receiving a frame
    def set_frames_written(*args, **kwargs) -> None:
        set_mock_value(fake_eiger.od.fp.frames_written, 1)

    callback_on_mock_put(fake_eiger.detector.trigger, set_frames_written)

    run_engine(
        configure_arm_trigger_and_disarm_detector(
            fake_eiger, eiger_params, trigger_info
        )
    )

    arm_mock = get_mock(fake_eiger.arm_when_ready)
    disarm_mock = get_mock(fake_eiger.detector.disarm)

    # Eiger was armed
    assert len(arm_mock.mock_calls) == 1
    # Disarm occurs at the start and end of the plan.
    assert len(disarm_mock.mock_calls) == 2
    assert (
        await fake_eiger.detector.photon_energy.get_value()
        == eiger_params.expected_energy_ev
    )
