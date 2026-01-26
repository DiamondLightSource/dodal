from unittest.mock import AsyncMock

import pytest
from bluesky.plan_stubs import mv, stop
from bluesky.protocols import Location
from bluesky.run_engine import RunEngine
from ophyd_async.core import StrictEnum, init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.i05.common_mirror import (
    XYZPiezoCollimatingMirror,
    XYZPiezoSwitchingMirror,
    XYZSwitchingMirror,
)


class MirrorEnum(StrictEnum):
    UNKNOWN = "Unknown"
    MJ6 = "MJ6"
    M3 = "M3"
    REFERENCE = "Reference"


@pytest.fixture
async def xyz_piezo_coll_mirror() -> XYZPiezoCollimatingMirror:
    async with init_devices(mock=True):
        xyz_piezo_coll_mirror = XYZPiezoCollimatingMirror("")
    return xyz_piezo_coll_mirror


@pytest.fixture
async def xyz_switching_mirror() -> XYZSwitchingMirror[MirrorEnum]:
    async with init_devices(mock=True):
        xyz_switching_mirror = XYZSwitchingMirror("", MirrorEnum)
    return xyz_switching_mirror


@pytest.fixture
async def xyz_piezo_switching_mirror() -> XYZPiezoSwitchingMirror[MirrorEnum]:
    async with init_devices(mock=True):
        xyz_piezo_switching_mirror = XYZPiezoSwitchingMirror("", MirrorEnum)
    return xyz_piezo_switching_mirror


@pytest.mark.parametrize(
    "x, y, z, pitch, yaw, roll, fpitch",
    [
        (0, 0, 0, 0, 0, 0, 0),
        (1.23, 2.40, 0.0, 0.0, 0.0, 0.0, 0.0),
        (1.23, 2.40, 3.51, 24.06, 12.02, 3.56, 13.23),
    ],
)
async def test_setting_xyz_piezo_coll_mirror_positions(
    xyz_piezo_coll_mirror: XYZPiezoCollimatingMirror,
    x: float,
    y: float,
    z: float,
    pitch: float,
    yaw: float,
    roll: float,
    fpitch: float,
):
    """
    Test setting positions on the Table using the ophyd_async mock tools.
    """
    # Call set to update the position
    set_mock_value(xyz_piezo_coll_mirror.x.user_readback, x)
    set_mock_value(xyz_piezo_coll_mirror.y.user_readback, y)
    set_mock_value(xyz_piezo_coll_mirror.z.user_readback, z)
    set_mock_value(xyz_piezo_coll_mirror.pitch.user_readback, pitch)
    set_mock_value(xyz_piezo_coll_mirror.yaw.user_readback, yaw)
    set_mock_value(xyz_piezo_coll_mirror.roll.user_readback, roll)
    set_mock_value(xyz_piezo_coll_mirror.fine_pitch, fpitch)

    await assert_reading(
        xyz_piezo_coll_mirror,
        {
            "xyz_piezo_coll_mirror-x": partial_reading(x),
            "xyz_piezo_coll_mirror-y": partial_reading(y),
            "xyz_piezo_coll_mirror-z": partial_reading(z),
            "xyz_piezo_coll_mirror-pitch": partial_reading(pitch),
            "xyz_piezo_coll_mirror-yaw": partial_reading(yaw),
            "xyz_piezo_coll_mirror-roll": partial_reading(roll),
            "xyz_piezo_coll_mirror-fine_pitch": partial_reading(fpitch),
        },
    )


@pytest.mark.parametrize(
    "x, y, z, pitch, yaw, roll, mirror",
    [
        (0, 0, 0, 0, 0, 0, MirrorEnum.UNKNOWN),
        (1.23, 2.40, 0.0, 0.0, 0.0, 0.0, MirrorEnum.M3),
        (1.23, 2.40, 3.51, 24.06, 12.02, 3.56, MirrorEnum.REFERENCE),
    ],
)
async def test_setting_xyz_switching_mirror_position_table(
    xyz_switching_mirror: XYZSwitchingMirror,
    x: float,
    y: float,
    z: float,
    pitch: float,
    yaw: float,
    roll: float,
    mirror: MirrorEnum,
):
    """
    Test setting positions on the Table using the ophyd_async mock tools.
    """
    # Call set to update the position
    set_mock_value(xyz_switching_mirror.x.user_readback, x)
    set_mock_value(xyz_switching_mirror.y.user_readback, y)
    set_mock_value(xyz_switching_mirror.z.user_readback, z)
    set_mock_value(xyz_switching_mirror.pitch.user_readback, pitch)
    set_mock_value(xyz_switching_mirror.yaw.user_readback, yaw)
    set_mock_value(xyz_switching_mirror.roll.user_readback, roll)
    set_mock_value(xyz_switching_mirror.mirror, mirror)

    await assert_reading(
        xyz_switching_mirror,
        {
            "xyz_switching_mirror-x": partial_reading(x),
            "xyz_switching_mirror-y": partial_reading(y),
            "xyz_switching_mirror-z": partial_reading(z),
            "xyz_switching_mirror-pitch": partial_reading(pitch),
            "xyz_switching_mirror-yaw": partial_reading(yaw),
            "xyz_switching_mirror-roll": partial_reading(roll),
            "xyz_switching_mirror-mirror": partial_reading(mirror),
        },
    )


async def test_move_xyz_switching_mirror(
    xyz_switching_mirror: XYZSwitchingMirror,
    run_engine: RunEngine,
):
    assert await xyz_switching_mirror.mirror.get_value() == MirrorEnum.UNKNOWN
    run_engine(mv(xyz_switching_mirror, MirrorEnum.M3))
    assert await xyz_switching_mirror.mirror.get_value() == MirrorEnum.M3


async def test_locate_xyz_switching_mirror(
    xyz_switching_mirror: XYZSwitchingMirror,
    run_engine: RunEngine,
):
    assert await xyz_switching_mirror.locate() == Location(
        setpoint=MirrorEnum.UNKNOWN, readback=MirrorEnum.UNKNOWN
    )
    run_engine(mv(xyz_switching_mirror, MirrorEnum.M3))
    assert await xyz_switching_mirror.locate() == Location(
        setpoint=MirrorEnum.M3, readback=MirrorEnum.M3
    )


async def test_stop_xyz_switching_mirror(
    xyz_switching_mirror: XYZSwitchingMirror,
    run_engine: RunEngine,
):
    xyz_switching_mirror.mirror_abort.trigger = AsyncMock()
    run_engine(stop(xyz_switching_mirror))
    xyz_switching_mirror.mirror_abort.trigger.assert_awaited_once()


@pytest.mark.parametrize(
    "x, y, z, pitch, yaw, roll,fpitch, mirror",
    [
        (0, 0, 0, 0, 0, 0, 0, MirrorEnum.UNKNOWN),
        (1.23, 2.40, 0.21, 0.0, 0.0, 0.0, 0.0, MirrorEnum.M3),
        (1.23, 2.40, 3.51, 24.06, 12.02, 3.56, 1.81, MirrorEnum.REFERENCE),
    ],
)
async def test_setting_xyz_piezo_switching_mirror_positions(
    xyz_piezo_switching_mirror: XYZPiezoSwitchingMirror,
    x: float,
    y: float,
    z: float,
    pitch: float,
    yaw: float,
    roll: float,
    fpitch: float,
    mirror: MirrorEnum,
):
    """
    Test setting positions on the Table using the ophyd_async mock tools.
    """
    # Call set to update the position
    set_mock_value(xyz_piezo_switching_mirror.x.user_readback, x)
    set_mock_value(xyz_piezo_switching_mirror.y.user_readback, y)
    set_mock_value(xyz_piezo_switching_mirror.z.user_readback, z)
    set_mock_value(xyz_piezo_switching_mirror.pitch.user_readback, pitch)
    set_mock_value(xyz_piezo_switching_mirror.yaw.user_readback, yaw)
    set_mock_value(xyz_piezo_switching_mirror.roll.user_readback, roll)
    set_mock_value(xyz_piezo_switching_mirror.fine_pitch, fpitch)
    set_mock_value(xyz_piezo_switching_mirror.mirror, mirror)

    await assert_reading(
        xyz_piezo_switching_mirror,
        {
            "xyz_piezo_switching_mirror-x": partial_reading(x),
            "xyz_piezo_switching_mirror-y": partial_reading(y),
            "xyz_piezo_switching_mirror-z": partial_reading(z),
            "xyz_piezo_switching_mirror-pitch": partial_reading(pitch),
            "xyz_piezo_switching_mirror-yaw": partial_reading(yaw),
            "xyz_piezo_switching_mirror-roll": partial_reading(roll),
            "xyz_piezo_switching_mirror-fine_pitch": partial_reading(fpitch),
            "xyz_piezo_switching_mirror-mirror": partial_reading(mirror),
        },
    )


async def test_move_xyz_piezo_switching_mirror(
    xyz_piezo_switching_mirror: XYZPiezoSwitchingMirror,
    run_engine: RunEngine,
):
    assert await xyz_piezo_switching_mirror.mirror.get_value() == MirrorEnum.UNKNOWN
    run_engine(mv(xyz_piezo_switching_mirror, MirrorEnum.M3))
    assert await xyz_piezo_switching_mirror.mirror.get_value() == MirrorEnum.M3


async def test_locate_xyz_piezo_switching_mirror(
    xyz_piezo_switching_mirror: XYZPiezoSwitchingMirror,
    run_engine: RunEngine,
):
    assert await xyz_piezo_switching_mirror.locate() == Location(
        setpoint=MirrorEnum.UNKNOWN, readback=MirrorEnum.UNKNOWN
    )
    run_engine(mv(xyz_piezo_switching_mirror, MirrorEnum.M3))
    assert await xyz_piezo_switching_mirror.locate() == Location(
        setpoint=MirrorEnum.M3, readback=MirrorEnum.M3
    )


async def test_stop_xyz_piezo_switching_mirror(
    xyz_piezo_switching_mirror: XYZPiezoSwitchingMirror,
    run_engine: RunEngine,
):
    xyz_piezo_switching_mirror.mirror_abort.trigger = AsyncMock()
    run_engine(stop(xyz_piezo_switching_mirror))
    xyz_piezo_switching_mirror.mirror_abort.trigger.assert_awaited_once()
