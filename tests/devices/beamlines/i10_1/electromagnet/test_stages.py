from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i10_1 import ElectromagnetStage


async def test_electronmagnet_stage_read():
    with init_devices(mock=True):
        mock_em_stage = ElectromagnetStage(prefix="BLXX-EA-EMAG-01:")
    await assert_reading(
        mock_em_stage,
        {
            "mock_em_stage-y": partial_reading(0.0),
            "mock_em_stage-pitch": partial_reading(0.0),
        },
    )
