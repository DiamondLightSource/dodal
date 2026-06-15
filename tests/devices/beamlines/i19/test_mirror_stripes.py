import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i19.mirror_stripes import MirrorStripes, StripeChoice


@pytest.fixture
def mirror_stripes() -> MirrorStripes:
    with init_devices(mock=True):
        stripes = MirrorStripes("", "mock_stripes")
    set_mock_value(stripes.stripe_choice, StripeChoice.EH1_RH)
    set_mock_value(stripes.error_code, 0)
    set_mock_value(stripes.error_message, "No error")
    return stripes


async def test_read_device(mirror_stripes: MirrorStripes):
    await assert_reading(
        mirror_stripes,
        {
            "mock_stripes-stripe_choice": partial_reading(StripeChoice.EH1_RH),
            "mock_stripes-is_busy": partial_reading(0),
            "mock_stripes-error_code": partial_reading(0),
            "mock_stripes-error_message": partial_reading("No error"),
        },
    )


@pytest.mark.parametrize(
    "new_stripe", [StripeChoice.EH2_SI, StripeChoice.EH1_PT, StripeChoice.EH2_RH]
)
async def test_change_stripe(new_stripe: StripeChoice, mirror_stripes: MirrorStripes):
    await mirror_stripes.stripe_choice.set(new_stripe)

    assert await mirror_stripes.stripe_choice.get_value() == new_stripe
