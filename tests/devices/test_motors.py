import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, set_mock_value

from dodal.devices.motors import XThetaStage, XYStage, XYZThetaStage


@pytest.fixture
async def xyzt_stage() -> XYZThetaStage:
    async with init_devices(mock=True):
        xyzt_stage = XYZThetaStage("")
    return xyzt_stage


@pytest.fixture
async def xy_stage() -> XYStage:
    async with init_devices(mock=True):
        xy_stage = XYStage("")
    return xy_stage


@pytest.fixture
async def xtheta_stage() -> XThetaStage:
    async with init_devices(mock=True):
        xtheta_stage = XThetaStage("")
    return xtheta_stage


async def test_setting_xy_position_table(xyzt_stage: XYZThetaStage):
    """
    Test setting x and y positions on the Table using the ophyd_async mock tools.
    """

    await assert_reading(
        xyzt_stage,
        {
            "xyzt_stage-x": {
                "value": 0.0,
            },
            "xyzt_stage-y": {
                "value": 0.0,
            },
            "xyzt_stage-z": {
                "value": 0.0,
            },
            "xyzt_stage-theta": {
                "value": 0.0,
            },
        },
    )

    # Call set to update the position
    set_mock_value(xyzt_stage.x.user_readback, 1.23)
    set_mock_value(xyzt_stage.y.user_readback, 4.56)

    await assert_reading(
        xyzt_stage,
        {
            "xyzt_stage-x": {
                "value": 1.23,
            },
            "xyzt_stage-y": {
                "value": 4.56,
            },
            "xyzt_stage-z": {
                "value": 0,
            },
            "xyzt_stage-theta": {
                "value": 0.0,
            },
        },
    )


async def test_setting_xyztheta_position_table(xyzt_stage: XYZThetaStage):
    """
    Test setting x and y positions on the Table using the ophyd_async mock tools.
    """
    await assert_reading(
        xyzt_stage,
        {
            "xyzt_stage-x": {
                "value": 0.0,
            },
            "xyzt_stage-y": {
                "value": 0.0,
            },
            "xyzt_stage-z": {
                "value": 0.0,
            },
            "xyzt_stage-theta": {
                "value": 0.0,
            },
        },
    )

    # Call set to update the position
    set_mock_value(xyzt_stage.x.user_readback, 1.23)
    set_mock_value(xyzt_stage.y.user_readback, 4.56)
    set_mock_value(xyzt_stage.z.user_readback, 7.89)
    set_mock_value(xyzt_stage.theta.user_readback, 10.11)

    await assert_reading(
        xyzt_stage,
        {
            "xyzt_stage-x": {
                "value": 1.23,
            },
            "xyzt_stage-y": {
                "value": 4.56,
            },
            "xyzt_stage-z": {
                "value": 7.89,
            },
            "xyzt_stage-theta": {
                "value": 10.11,
            },
        },
    )


async def test_setting(xy_stage: XYStage):
    """
    Test setting x and y positions on the XYStage using ophyd_async mock tools.
    """

    await assert_reading(
        xy_stage,
        {"xy_stage-x": {"value": 0.0}, "xy_stage-y": {"value": 0.0}},
    )

    # Call set to update the position
    set_mock_value(xy_stage.x.user_readback, 5)
    set_mock_value(xy_stage.y.user_readback, 5)

    await assert_reading(
        xy_stage,
        {"xy_stage-x": {"value": 5.0}, "xy_stage-y": {"value": 5.0}},
    )


async def test_reading_training_rig(xtheta_stage: XThetaStage):
    await assert_reading(
        xtheta_stage,
        {
            "xtheta_stage-x": {
                "value": 0.0,
            },
            "xtheta_stage-theta": {
                "value": 0.0,
            },
        },
    )
