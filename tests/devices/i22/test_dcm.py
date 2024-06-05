from unittest.mock import ANY

import pytest
from bluesky.protocols import Reading
from ophyd_async.core import DeviceCollector, assert_configuration, assert_reading

from dodal.devices.i22.dcm import (
    CrystalMetadata,
    DoubleCrystalMonochromator,
    MonochromatingCrystal,
)


@pytest.fixture
async def dcm() -> DoubleCrystalMonochromator:
    async with DeviceCollector(mock=True):
        dcm = DoubleCrystalMonochromator(
            "FOO",
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


@pytest.mark.parametrize(
    "metadata,expected_absent",
    [
        (
            CrystalMetadata(),
            {
                "crystal-usage",
                "crystal-type",
                "crystal-reflection",
                "crystal-d_spacing",
            },
        ),
        (
            CrystalMetadata(usage="Bragg"),
            {
                "crystal-type",
                "crystal-reflection",
                "crystal-d_spacing",
            },
        ),
        (
            CrystalMetadata(usage="Bragg", reflection=[1, 1, 1]),
            {
                "crystal-type",
                "crystal-d_spacing",
            },
        ),
    ],
)
async def test_crystal_metadata_not_propagated_when_not_supplied(
    metadata: CrystalMetadata,
    expected_absent: set[str],
):
    async with DeviceCollector(mock=True):
        crystal = MonochromatingCrystal("FOO", metadata=metadata)

    configuration = await crystal.read_configuration()
    assert expected_absent.isdisjoint(configuration)


async def test_reading(dcm: DoubleCrystalMonochromator):
    await assert_reading(
        dcm,
        {
            "dcm-energy": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-bragg": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-perp_temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-backplate_temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-offset": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1-pitch": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1-roll": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1-heater_temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1-temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2-pitch": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2-roll": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2-heater_temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2-temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-perp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
        },
    )


async def test_configuration(dcm: DoubleCrystalMonochromator):
    await assert_configuration(
        dcm,
        {
            "dcm-crystal_1-roll-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1-roll-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1-pitch-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1-pitch-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1-reflection": {
                "value": (1, 1, 1),
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1-type": {
                "value": "silicon",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1-d_spacing": {
                "value": 3.13475,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1-usage": {
                "value": "Bragg",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-bragg-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-bragg-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-energy-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-energy-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-perp-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-perp-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2-roll-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2-roll-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2-pitch-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2-pitch-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2-reflection": {
                "value": (1, 1, 1),
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2-type": {
                "value": "silicon",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2-d_spacing": {
                "value": 3.13475,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2-usage": {
                "value": "Bragg",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-offset-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-offset-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
        },
    )
