from unittest.mock import ANY

import pytest
from ophyd_async.core import (
    DeviceCollector,
    assert_configuration,
    assert_reading,
    set_mock_value,
)

from dodal.devices.i22.dcm import CrystalMetadata, DoubleCrystalMonochromator


@pytest.fixture
async def dcm() -> DoubleCrystalMonochromator:
    async with DeviceCollector(mock=True):
        dcm = DoubleCrystalMonochromator(
            motion_prefix="FOO-MO",
            temperature_prefix="FOO-DI",
            crystal_1_metadata=CrystalMetadata(
                usage="Bragg",
                type="silicon",
                reflection=(1, 1, 1),
                d_spacing=3.13475,
            ),
            crystal_2_metadata=CrystalMetadata(
                usage="Bragg",
                type="silicon",
                reflection=(1, 1, 1),
                d_spacing=3.13475,
            ),
        )

    return dcm


async def test_crystal_metadata_not_propagated_when_not_supplied():
    async with DeviceCollector(mock=True):
        dcm = DoubleCrystalMonochromator(
            motion_prefix="FOO-MO",
            temperature_prefix="FOO-DI",
            crystal_1_metadata=None,
            crystal_2_metadata=None,
        )

    configuration = await dcm.read_configuration()
    expected_absent_keys = {
        "crystal-1-usage",
        "crystal-1-type",
        "crystal-1-reflection",
        "crystal-1-d_spacing",
        "crystal-2-usage",
        "crystal-2-type",
        "crystal-2-reflection",
        "crystal-2-d_spacing",
    }
    assert expected_absent_keys.isdisjoint(configuration)


@pytest.mark.parametrize(
    "energy,wavelength",
    [
        (0.0, 0.0),
        (1.0, 12.3984),
        (2.0, 6.1992),
    ],
)
async def test_wavelength(
    dcm: DoubleCrystalMonochromator,
    energy: float,
    wavelength: float,
):
    set_mock_value(dcm.energy.user_readback, energy)
    reading = await dcm.read()
    assert reading["dcm-wavelength"]["value"] == wavelength


async def test_reading(dcm: DoubleCrystalMonochromator):
    await assert_reading(
        dcm,
        {
            "dcm-backplate_temp": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-bragg": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_1_heater_temp": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_1_roll": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_1_temp": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_2_heater_temp": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_2_pitch": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_2_roll": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_2_temp": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-energy": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-offset": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-perp": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-perp_temp": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-wavelength": {
                "timestamp": ANY,
                "value": 0.0,
            },
        },
    )


async def test_configuration(dcm: DoubleCrystalMonochromator):
    await assert_configuration(
        dcm,
        {
            "dcm-bragg-motor_egu": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": "",
            },
            "dcm-bragg-velocity": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_1_d_spacing": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 3.13475,
            },
            "dcm-crystal_1_reflection": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": (1, 1, 1),
            },
            "dcm-crystal_1_roll-motor_egu": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": "",
            },
            "dcm-crystal_1_roll-velocity": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_1_type": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": "silicon",
            },
            "dcm-crystal_1_usage": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": "Bragg",
            },
            "dcm-crystal_2_d_spacing": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 3.13475,
            },
            "dcm-crystal_2_pitch-motor_egu": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": "",
            },
            "dcm-crystal_2_pitch-velocity": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_2_reflection": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": (1, 1, 1),
            },
            "dcm-crystal_2_roll-motor_egu": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": "",
            },
            "dcm-crystal_2_roll-velocity": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_2_type": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": "silicon",
            },
            "dcm-crystal_2_usage": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": "Bragg",
            },
            "dcm-energy-motor_egu": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": "",
            },
            "dcm-energy-velocity": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-offset-motor_egu": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": "",
            },
            "dcm-offset-velocity": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-perp-motor_egu": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": "",
            },
            "dcm-perp-velocity": {
                "alarm_severity": ANY,
                "timestamp": ANY,
                "value": 0.0,
            },
        },
    )
