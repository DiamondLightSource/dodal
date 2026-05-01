import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.interlocks import (
    EnumPLCInterlock,
    IntPLCInterlock,
    PLCInterlockState,
    PSSInterlock,
)


@pytest.fixture
async def pss_interlock() -> PSSInterlock:
    async with init_devices(mock=True):
        interlock = PSSInterlock(bl_prefix="TEST")
    return interlock


@pytest.fixture
async def enum_plc_interlock() -> EnumPLCInterlock:
    async with init_devices(mock=True):
        interlock = EnumPLCInterlock(bl_prefix="TEST")
    return interlock


@pytest.fixture
async def int_plc_interlock() -> IntPLCInterlock:
    async with init_devices(mock=True):
        interlock = IntPLCInterlock(bl_prefix="TEST")
    return interlock


async def test_pss_interlock_is_readable(pss_interlock: PSSInterlock):
    await assert_reading(
        pss_interlock,
        {
            f"{pss_interlock.name}-is_safe": partial_reading(True),
            f"{pss_interlock.name}-status": partial_reading(0.0),
        },
    )


async def test_enum_plc_interlock_is_readable(enum_plc_interlock: EnumPLCInterlock):
    await assert_reading(
        enum_plc_interlock,
        {
            f"{enum_plc_interlock.name}-is_safe": partial_reading(False),
            f"{enum_plc_interlock.name}-status": partial_reading(
                PLCInterlockState.FAILED
            ),
        },
    )


async def test_int_plc_interlock_is_readable(int_plc_interlock: IntPLCInterlock):
    await assert_reading(
        int_plc_interlock,
        {
            f"{int_plc_interlock.name}-is_safe": partial_reading(False),
            f"{int_plc_interlock.name}-status": partial_reading(0),
        },
    )


@pytest.mark.parametrize(
    "readback, expected_state",
    [
        (0.0, True),
        (1.0, False),
        (7.0, False),
    ],
)
async def test_pss_interlock_safe_to_operate_logic(
    pss_interlock: PSSInterlock,
    readback: float,
    expected_state: bool,
):
    set_mock_value(pss_interlock.status, readback)
    assert await pss_interlock.is_safe.get_value() is expected_state


@pytest.mark.parametrize(
    "readback, expected_state",
    [
        (PLCInterlockState.OK, True),
        (PLCInterlockState.RUN_ILKS_OK, True),
        (PLCInterlockState.DISARMED, False),
        (PLCInterlockState.FAILED, False),
    ],
)
async def test_enum_plc_interlock_safe_to_operate_logic(
    enum_plc_interlock: EnumPLCInterlock,
    readback: float,
    expected_state: bool,
):
    set_mock_value(enum_plc_interlock.status, readback)
    assert await enum_plc_interlock.is_safe.get_value() is expected_state


@pytest.mark.parametrize(
    "readback, expected_state",
    [
        (65535, True),
        (0, False),
    ],
)
async def test_int_plc_interlock_safe_to_opperate_logic(
    int_plc_interlock: IntPLCInterlock,
    readback: float,
    expected_state: bool,
):
    set_mock_value(int_plc_interlock.status, readback)
    assert await int_plc_interlock.is_safe.get_value() is expected_state
