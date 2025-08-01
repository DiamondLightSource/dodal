from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DetectorTrigger, TriggerInfo
from ophyd_async.fastcs.eiger import EigerDetector as FastEiger
from ophyd_async.testing import callback_on_mock_put, set_mock_value

from dodal.plans.configure_arm_trigger_and_disarm_detector import (
    configure_arm_trigger_and_disarm_detector,
)


@pytest.fixture
async def fake_eiger():
    fake_eiger = FastEiger("", MagicMock())
    await fake_eiger.connect(mock=True)
    fake_eiger.drv.detector.arm.trigger = AsyncMock()
    fake_eiger.drv.detector.disarm.trigger = AsyncMock()
    fake_eiger._writer.observe_indices_written = fake_observe_indices_written
    return fake_eiger


async def fake_observe_indices_written(timeout: float) -> AsyncGenerator[int, None]:
    yield 1


async def test_configure_arm_trigger_and_disarm_detector(
    fake_eiger, eiger_params, RE: RunEngine
):
    trigger_info = TriggerInfo(
        # Manual trigger, so setting number of triggers to 1.
        number_of_events=1,
        trigger=DetectorTrigger.INTERNAL,
        deadtime=0.0001,
    )
    filename: str = "filename.h5"
    fake_eiger._writer._path_provider.return_value.filename = filename

    def set_meta_active(*args, **kwargs) -> None:
        set_mock_value(fake_eiger.odin.meta_file_name, filename)
        set_mock_value(fake_eiger.odin.id, filename)
        set_mock_value(fake_eiger.odin.meta_active, "Active")

    def set_capture_rbv_meta_writing_and_detector_state(*args, **kwargs) -> None:
        # Mimics capturing and immediete completion status on Eiger.
        fake_eiger._writer._path_provider.return_value.filename = "filename.h5"
        set_mock_value(fake_eiger.odin.capture_rbv, "Capturing")
        set_mock_value(fake_eiger.odin.meta_writing, "Writing")
        set_mock_value(fake_eiger.odin.meta_file_name, "filename.h5")
        set_mock_value(fake_eiger.odin.id, "filename.h5")
        set_mock_value(fake_eiger.odin.fan_ready, 1)
        set_mock_value(fake_eiger.drv.detector.state, "idle")

    callback_on_mock_put(fake_eiger.odin.num_to_capture, set_meta_active)
    callback_on_mock_put(
        fake_eiger.odin.capture, set_capture_rbv_meta_writing_and_detector_state
    )

    RE(
        configure_arm_trigger_and_disarm_detector(
            fake_eiger, eiger_params, trigger_info
        )
    )
    fake_eiger.drv.detector.arm.trigger.assert_called_once()
    # Disarm occurs at the start and end of the plan.
    assert len(fake_eiger.drv.detector.disarm.trigger.call_args_list) == 2
    assert (
        await fake_eiger.drv.detector.photon_energy.get_value()
        == eiger_params.expected_energy_ev
    )
