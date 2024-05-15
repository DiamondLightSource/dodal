from unittest.mock import ANY

import pytest
from ophyd_async.core import (
    DeviceCollector,
    assert_configuration,
    assert_reading,
)

from dodal.devices.dcm import DCM, DCMCrystal

CRYSTAL = DCMCrystal(
    usage="Bragg",
    type="Silicon",
    reflection=(1, 1, 1),
    d_spacing=3.13475,
)


@pytest.fixture
async def dcm() -> DCM:
    async with DeviceCollector(mock=True):
        dcm = DCM("DCM-01", name="dcm", crystal=CRYSTAL)
    return dcm


async def test_reading_includes_read_fields(dcm: DCM):
    await assert_reading(
        dcm,
        {
            "dcm-roll_in_mrad": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-perp_in_mm": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-offset_in_mm": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-xtal2_temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-perp_temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-perp_sub_assembly_temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-xtal2_heater_temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-xtal1_temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-energy_in_kev": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-pitch_in_mrad": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-backplate_temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-wavelength": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-bragg_in_degrees": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-xtal1_heater_temp": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
        },
    )


async def test_configuration_includes_configuration_fields(dcm: DCM):
    await assert_configuration(
        dcm,
        {
            "dcm-roll_in_mrad-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-roll_in_mrad-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-perp_in_mm-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-perp_in_mm-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-offset_in_mm-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-offset_in_mm-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-energy_in_kev-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-energy_in_kev-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-pitch_in_mrad-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-pitch_in_mrad-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-wavelength-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-wavelength-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-bragg_in_degrees-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-bragg_in_degrees-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_d_spacing": {
                "value": 3.13475,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_reflection": {
                "value": (1, 1, 1),
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_type": {
                "value": "Silicon",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_usage": {
                "value": "Bragg",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
        },
    )


@pytest.mark.parametrize("crystal", [DCMCrystal(), None])
async def test_crystal_data_not_propagated_when_not_supplied(
    crystal: DCMCrystal | None,
):
    async with DeviceCollector(mock=True):
        dcm = DCM("DCM-01", name="dcm", crystal=crystal)

    configuration = await dcm.read_configuration()
    assert {
        "dcm-crystal_usage",
        "dcm-crystal_type",
        "dcm-crystal_reflection",
        "dcm-crystal_d_spacing",
    }.isdisjoint(configuration)
