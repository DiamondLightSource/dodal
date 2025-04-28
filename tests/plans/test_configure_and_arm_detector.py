from unittest.mock import AsyncMock, MagicMock

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DetectorTrigger
from ophyd_async.fastcs.eiger import EigerDetector as FastEiger
from ophyd_async.fastcs.eiger import EigerTriggerInfo
from ophyd_async.testing import callback_on_mock_put, set_mock_value

from dodal.plans.configure_and_arm_detector import (
    configure_and_arm_detector,
)


@pytest.fixture
async def fake_eiger():
    fake_eiger = FastEiger("", MagicMock())
    await fake_eiger.connect(mock=True)
    fake_eiger.drv.detector.arm.trigger = AsyncMock()
    return fake_eiger


async def test_configure_and_arm_detector(fake_eiger, eiger_params, RE: RunEngine):
    trigger_info = EigerTriggerInfo(
        number_of_events=eiger_params.num_triggers,
        energy_ev=eiger_params.expected_energy_ev,
        trigger=DetectorTrigger.EDGE_TRIGGER,
        deadtime=0.0001,
    )

    def set_meta_active(*args, **kwargs) -> None:
        set_mock_value(fake_eiger.odin.meta_active, "Active")

    def set_capture_rbv_and_meta_writing(*args, **kwargs) -> None:
        set_mock_value(fake_eiger.odin.capture_rbv, "Capturing")
        set_mock_value(fake_eiger.odin.meta_writing, "Writing")

    callback_on_mock_put(fake_eiger.odin.num_to_capture, set_meta_active)
    callback_on_mock_put(fake_eiger.odin.capture, set_capture_rbv_and_meta_writing)

    RE(configure_and_arm_detector(fake_eiger, eiger_params, trigger_info))
    fake_eiger.drv.detector.arm.trigger.assert_called_once()
    assert (
        await fake_eiger.drv.detector.photon_energy.get_value()
        == eiger_params.expected_energy_ev
    )
