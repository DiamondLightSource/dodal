import pytest
from ophyd_async.core import (
    YesNo,
    callback_on_mock_put,
    get_mock_put,
    init_devices,
    set_mock_value,
)
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.fast_shutter import OpenClose
from dodal.devices.zebra.zebra_controlled_shutter import (
    MXZebraShutter,
    ZebraFastShutter,
    ZebraShutterControl,
    ZebraShutterState,
)


@pytest.fixture
async def sim_shutter():
    async with init_devices(mock=True):
        sim_shutter = MXZebraShutter(
            prefix="sim_shutter",
            name="shutter",
        )

    def propagate_status(value: ZebraShutterState, *args, **kwargs):
        set_mock_value(sim_shutter.position_readback, value)

    callback_on_mock_put(sim_shutter._manual_position_setpoint, propagate_status)
    return sim_shutter


@pytest.mark.parametrize("new_state", [ZebraShutterState.OPEN, ZebraShutterState.CLOSE])
async def test_set_shutter_open(
    sim_shutter: MXZebraShutter, new_state: ZebraShutterState
):
    await sim_shutter.set(new_state)
    reading = await sim_shutter.read()

    shutter_position = reading.get("shutter-position_readback", {})
    assert shutter_position["value"] is new_state, (
        f"Unexpected value: {shutter_position['value']}"
    )


async def test_given_shutter_in_auto_then_when_set_raises(sim_shutter: MXZebraShutter):
    set_mock_value(sim_shutter.control_mode, ZebraShutterControl.AUTO)
    with pytest.raises(UserWarning):
        await sim_shutter.set(ZebraShutterState.OPEN)


@pytest.fixture
def int_fast_shutter() -> ZebraFastShutter:
    with init_devices(mock=True):
        shutter = ZebraFastShutter(set_pv="SET", get_pv="GET")
    return shutter


@pytest.mark.parametrize(
    "pv_value, expected_reading",
    [
        [0, OpenClose.CLOSE],
        [1, OpenClose.OPEN],
    ],
)
async def test_given_fast_shutter_pv_at_int_then_reads_expected_enum(
    int_fast_shutter: ZebraFastShutter, pv_value: int, expected_reading: OpenClose
):
    set_mock_value(int_fast_shutter._get_pv, pv_value)

    await assert_reading(
        int_fast_shutter,
        {
            f"{int_fast_shutter.name}-shutter_state": partial_reading(expected_reading),
        },
    )


@pytest.mark.parametrize(
    "fast_shutter_state, expected_pv_value",
    [
        [OpenClose.CLOSE, YesNo.NO],
        [OpenClose.OPEN, YesNo.YES],
    ],
)
async def test_when_fast_shutter_state_changed_then_pv_set_correctly(
    int_fast_shutter: ZebraFastShutter,
    fast_shutter_state: OpenClose,
    expected_pv_value: int,
):
    await int_fast_shutter.set(fast_shutter_state)

    mock = get_mock_put(int_fast_shutter._set_pv)
    mock.assert_called_once_with(expected_pv_value)


@pytest.mark.parametrize(
    "initial_readback_pv_state, initial_setpoint_pv_state, set_fast_shutter_state",
    [
        [1, YesNo.YES, OpenClose.CLOSE],
        [0, YesNo.NO, OpenClose.OPEN],
    ],
)
async def test_when_fast_shutter_state_changed_then_pv_readback_correct(
    int_fast_shutter: ZebraFastShutter,
    initial_readback_pv_state: int,
    initial_setpoint_pv_state: YesNo,
    set_fast_shutter_state: OpenClose,
):
    set_mock_value(int_fast_shutter._get_pv, initial_readback_pv_state)
    set_mock_value(int_fast_shutter._set_pv, initial_setpoint_pv_state)

    await int_fast_shutter.set(set_fast_shutter_state)

    await assert_reading(
        int_fast_shutter,
        {
            f"{int_fast_shutter.name}-shutter_state": partial_reading(
                set_fast_shutter_state
            ),
        },
    )
