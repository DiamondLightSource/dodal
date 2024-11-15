from ophyd_async.core import get_mock

from dodal.devices.laser_shaping.stages import GonioStages


async def test_stage_x_y():
    stages = GonioStages(prefix="LA18L-MO-LSR-01:")
    await stages.connect(mock=True)
    await stages.x.velocity.set(5)
    mock_velocity = get_mock(stages.x.velocity)
    mock_velocity.put.assert_called_once()
