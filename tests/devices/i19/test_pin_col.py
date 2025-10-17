from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import get_mock_put, set_mock_value

from dodal.devices.i19.pin_col_stages import (
    AperturePosition,
    PinColConfiguration,
    PinColRequest,
    PinholeCollimatorControl,
    _PinColPosition,
)
from dodal.devices.motors import XYStage
from dodal.testing import patch_all_motors


@pytest.fixture
async def pincol() -> AsyncGenerator[PinholeCollimatorControl]:
    async with init_devices(mock=True):
        pc = PinholeCollimatorControl("", "test_pincol")
    with patch_all_motors(pc):
        yield pc


def test_pincol_created_without_errors(pincol: PinholeCollimatorControl):
    assert isinstance(pincol, PinholeCollimatorControl)
    assert isinstance(pincol.mapt, PinColConfiguration)
    assert isinstance(pincol._pinhole, XYStage)
    assert isinstance(pincol._collimator, XYStage)


@pytest.mark.parametrize(
    "ap_request, in_positions, size",
    [
        (_PinColPosition.PCOL20, [12, 34, 7, 28], 20),
        (_PinColPosition.PCOL100, [15, 24, 10, 16], 100),
    ],
)
async def test_pincol_get_motor_positions_for_requested_aperture(
    ap_request: _PinColPosition,
    in_positions: list[float],
    size: int,
    pincol: PinholeCollimatorControl,
):
    set_mock_value(pincol.mapt.configuration.select_config, ap_request)
    set_mock_value(pincol.mapt.pin_x.in_positions[size], in_positions[0])
    set_mock_value(pincol.mapt.pin_y.in_positions[size], in_positions[1])
    set_mock_value(pincol.mapt.col_x.in_positions[size], in_positions[2])
    set_mock_value(pincol.mapt.col_y.in_positions[size], in_positions[3])

    positions = await pincol._get_motor_positions_for_requested_aperture(ap_request)

    assert isinstance(positions, AperturePosition)

    assert positions.pinhole_x == in_positions[0]
    assert positions.pinhole_y == in_positions[1]
    assert positions.collimator_x == in_positions[2]
    assert positions.collimator_y == in_positions[3]


async def test_when_move_out_only_x_motors_move(
    pincol: PinholeCollimatorControl,
):
    out_positions = [5.2, 3.5]
    set_mock_value(pincol.mapt.pin_x_out, out_positions[0])
    set_mock_value(pincol.mapt.col_x_out, out_positions[1])

    await pincol.set(PinColRequest.OUT)

    assert await pincol._pinhole.x.user_readback.get_value() == out_positions[0]
    assert await pincol._collimator.x.user_readback.get_value() == out_positions[1]

    # Verify y motors have not been asked to move
    assert await pincol._pinhole.y.user_setpoint.get_value() == 0
    assert await pincol._collimator.y.user_setpoint.get_value() == 0


async def test_when_move_out_motors_move_in_right_order(
    pincol: PinholeCollimatorControl,
):
    out_positions = [5.2, 3.5]
    set_mock_value(pincol.mapt.pin_x_out, out_positions[0])
    set_mock_value(pincol.mapt.col_x_out, out_positions[1])

    set_mock_value(pincol._pinhole.x.user_readback, 18)
    set_mock_value(pincol._pinhole.y.user_readback, 15)
    set_mock_value(pincol._collimator.x.user_readback, 22)
    set_mock_value(pincol._collimator.y.user_readback, 13)

    parent = MagicMock()
    parent.attach_mock(get_mock_put(pincol._pinhole.x.user_setpoint), "pinx")
    parent.attach_mock(get_mock_put(pincol._collimator.x.user_setpoint), "colx")

    await pincol.set(PinColRequest.OUT)

    assert len(parent.mock_calls) == 2
    parent.assert_has_calls([call.colx(3.5, wait=True), call.pinx(5.2, wait=True)])


@pytest.mark.parametrize(
    "ap_request, in_positions",
    [
        (PinColRequest.PCOL20, [12, 34, 7, 28]),
        (PinColRequest.PCOL100, [15, 24, 10, 16]),
    ],
)
async def test_move_in(
    ap_request: PinColRequest,
    in_positions: list[float],
    pincol: PinholeCollimatorControl,
):
    ap_positions = AperturePosition(
        pinhole_x=in_positions[0],
        pinhole_y=in_positions[1],
        collimator_x=in_positions[2],
        collimator_y=in_positions[3],
    )
    pincol._get_motor_positions_for_requested_aperture = AsyncMock(
        return_value=ap_positions
    )

    await pincol.set(ap_request)

    assert await pincol.mapt.configuration.select_config.get_value() == ap_request.value

    assert await pincol._pinhole.x.user_readback.get_value() == in_positions[0]
    assert await pincol._pinhole.y.user_readback.get_value() == in_positions[1]
    assert await pincol._collimator.x.user_readback.get_value() == in_positions[2]
    assert await pincol._collimator.y.user_readback.get_value() == in_positions[3]


async def test_when_move_in_motors_move_in_right_order(
    pincol: PinholeCollimatorControl,
):
    ap_positions = AperturePosition(
        pinhole_x=18, pinhole_y=15, collimator_x=22, collimator_y=13
    )
    pincol._get_motor_positions_for_requested_aperture = AsyncMock(
        return_value=ap_positions
    )

    parent = MagicMock()
    parent.attach_mock(get_mock_put(pincol._pinhole.x.user_setpoint), "pinx")
    parent.attach_mock(get_mock_put(pincol._pinhole.y.user_setpoint), "piny")
    parent.attach_mock(get_mock_put(pincol._collimator.x.user_setpoint), "colx")
    parent.attach_mock(get_mock_put(pincol._collimator.y.user_setpoint), "coly")

    await pincol.set(PinColRequest.PCOL40)

    assert len(parent.mock_calls) == 4
    parent.assert_has_calls(
        [
            call.pinx(18, wait=True),
            call.piny(15, wait=True),
            call.colx(22, wait=True),
            call.coly(13, wait=True),
        ]
    )
