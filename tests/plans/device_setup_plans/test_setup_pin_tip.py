import pytest
from bluesky import RunEngine
from ophyd_async.core import init_devices

from dodal.devices.oav.oav_parameters import OAVParameters
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.plans.device_setup_plans.setup_pin_tip_params import (
    setup_pin_tip_detection_params,
)
from tests.devices.oav.test_data import TEST_OAV_CENTRING_JSON


@pytest.fixture
def pin_tip_detection() -> PinTipDetection:
    with init_devices(mock=True):
        pin_tip = PinTipDetection("", "mock-pin-tip")
    return pin_tip


@pytest.fixture
def params() -> OAVParameters:
    return OAVParameters("pinTipCentring", TEST_OAV_CENTRING_JSON)


async def test_setup_pin_tip_from_params(
    pin_tip_detection: PinTipDetection, params: OAVParameters, run_engine: RunEngine
):
    run_engine(setup_pin_tip_detection_params(pin_tip_detection, params))

    assert await pin_tip_detection.preprocess_operation.get_value() == 8
