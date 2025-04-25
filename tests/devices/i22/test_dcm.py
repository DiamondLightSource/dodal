from unittest.mock import ANY

import bluesky.plans as bp
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_configuration,
    assert_emitted,
    assert_reading,
    set_mock_value,
)

from dodal.common.crystal_metadata import (
    MaterialsEnum,
    make_crystal_metadata_from_material,
)
from dodal.devices.i22.dcm import DCM


@pytest.fixture
async def dcm() -> DCM:
    metadata_1 = make_crystal_metadata_from_material(MaterialsEnum.Si, (1, 1, 1))
    metadata_2 = make_crystal_metadata_from_material(MaterialsEnum.Si, (1, 1, 1))
    async with init_devices(mock=True):
        dcm = DCM(
            prefix="FOO-MO",
            temperature_prefix="FOO-DI",
            crystal_1_metadata=metadata_1,
            crystal_2_metadata=metadata_2,
        )

    return dcm


def test_count_dcm(
    RE: RunEngine,
    run_engine_documents: dict[str, list[dict]],
    dcm: DCM,
):
    RE(bp.count([dcm]))
    assert_emitted(
        run_engine_documents,
        start=1,
        descriptor=1,
        event=1,
        stop=1,
    )


@pytest.mark.parametrize(
    "energy,wavelength",
    [
        (0.0, 0.0),
        (1.0, 12.3984),
        (2.0, 6.1992),
    ],
)
async def test_wavelength(
    dcm: DCM,
    energy: float,
    wavelength: float,
):
    set_mock_value(dcm.energy_in_kev.user_readback, energy)
    reading = await dcm.read()
    assert reading["dcm-wavelength_in_a"]["value"] == wavelength


@pytest.mark.skip("See https://github.com/bluesky/ophyd-async/issues/839")
async def test_reading(dcm: DCM):
    await assert_reading(
        dcm,
        {
            "dcm-backplate_temp": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-bragg_in_degrees": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_1_heater_temp": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystals-0-roll_in_mrad": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_1_temp": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_2_heater_temp": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystals-1-pitch_in_mrad": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystals-1-roll_in_mrad": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_2_temp": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-energy_in_kev": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-offset_in_mm": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-perp": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-perp_temp": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-wavelength_in_a": {
                "timestamp": ANY,
                "value": 0.0,
            },
            "dcm-crystal_metadata_d_spacing_a": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
        },
    )


@pytest.mark.skip(
    reason="https://github.com/bluesky/ophyd-async/issues/618 assert_configuration() on numpy arrays is "
    "broken"
)
async def test_configuration(dcm: DCM):
    await assert_configuration(
        dcm,
        {
            "dcm-bragg-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-bragg-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-energy-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-energy-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_1_roll-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_1_roll-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-offset-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-offset-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_2_pitch-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_2_pitch-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_2_roll-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_2_roll-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-perp-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-perp-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_2_d_spacing": {
                "value": 0.31356,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_2_usage": {
                "value": "Bragg",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_2_type": {
                "value": "silicon",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_1_reflection": {
                "value": [1, 1, 1],
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_2_reflection": {
                "value": [1, 1, 1],
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_1_d_spacing": {
                "value": 0.31356,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_1_usage": {
                "value": "Bragg",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "dcm-crystal_1_type": {
                "value": "silicon",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )
