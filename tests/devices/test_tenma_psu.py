from unittest.mock import call

import pytest
from ophyd_async.core import get_mock_put, init_devices, set_mock_value
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.tenma_psu import TenmaPSU


@pytest.fixture
async def tenma_psu() -> TenmaPSU:
    async with init_devices(mock=True):
        psu = TenmaPSU("TEST:", name="tenma")
    return psu


async def test_tenma_psu_reads_measurements_and_output_status(
    tenma_psu: TenmaPSU,
) -> None:
    set_mock_value(tenma_psu.voltage_readback, 12.5)
    set_mock_value(tenma_psu.current_readback, 0.75)
    set_mock_value(tenma_psu.power_readback, 9.375)

    await assert_reading(
        tenma_psu,
        {
            "tenma-voltage_readback": partial_reading(12.5),
            "tenma-current_readback": partial_reading(0.75),
            "tenma-power_readback": partial_reading(9.375),
        },
        False,
    )


async def test_tenma_psu_reads_setpoints_as_configuration(
    tenma_psu: TenmaPSU,
) -> None:
    set_mock_value(tenma_psu.voltage_sp, 12.0)
    set_mock_value(tenma_psu.current_sp, 1.5)

    await assert_configuration(
        tenma_psu,
        {
            "tenma-voltage_sp": partial_reading(12.0),
            "tenma-current_sp": partial_reading(1.5),
        },
    )


async def test_tenma_psu_output_controls(tenma_psu: TenmaPSU) -> None:
    await tenma_psu.output.set(True)
    await tenma_psu.output.set(False)

    get_mock_put(tenma_psu._output_on).assert_awaited_once_with(True)
    get_mock_put(tenma_psu._output_off).assert_awaited_once_with(True)


@pytest.mark.parametrize("output_state", [True, False])
async def test_tenma_psu_output_state_returns(
    tenma_psu: TenmaPSU, output_state: bool
) -> None:
    set_mock_value(tenma_psu._output_rbv, output_state)

    await assert_reading(
        tenma_psu,
        {"tenma-output": partial_reading(output_state)},
        False,
    )


async def test_tenma_psu_setpoints_write_values(tenma_psu: TenmaPSU) -> None:
    await tenma_psu.voltage_sp.set(12.0)
    await tenma_psu.current_sp.set(1.5)

    assert get_mock_put(tenma_psu.voltage_sp).await_args_list == [call(12.0)]
    assert get_mock_put(tenma_psu.current_sp).await_args_list == [call(1.5)]
