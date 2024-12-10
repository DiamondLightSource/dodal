from collections.abc import Mapping
from unittest.mock import ANY

import bluesky.plans as bp
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector
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
from dodal.devices.i22.dcm import DoubleCrystalMonochromator


@pytest.fixture
async def dcm() -> DoubleCrystalMonochromator:
    metadata_1 = make_crystal_metadata_from_material(MaterialsEnum.Si, (1, 1, 1))
    metadata_2 = make_crystal_metadata_from_material(MaterialsEnum.Si, (1, 1, 1))
    async with DeviceCollector(mock=True):
        dcm = DoubleCrystalMonochromator(
            prefix="FOO-MO",
            temperature_prefix="FOO-DI",
            crystal_1_metadata=metadata_1,
            crystal_2_metadata=metadata_2,
        )

    return dcm


def test_count_dcm(
    RE: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    dcm: DoubleCrystalMonochromator,
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


@pytest.mark.skip(
    reason="https://github.com/bluesky/ophyd-async/issues/618 assert_configuration() on numpy arrays is "
    "broken"
)
async def test_configuration(dcm: DoubleCrystalMonochromator):
    await assert_configuration(
        dcm,
        {
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
            "dcm-crystal_1_roll-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1_roll-velocity": {
                "value": 0.0,
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
            "dcm-crystal_2_pitch-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2_pitch-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2_roll-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2_roll-velocity": {
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
            "dcm-crystal_2_d_spacing": {
                "value": 0.31356,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2_usage": {
                "value": "Bragg",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2_type": {
                "value": "silicon",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1_reflection": {
                "value": [1, 1, 1],
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_2_reflection": {
                "value": [1, 1, 1],
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1_d_spacing": {
                "value": 0.31356,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1_usage": {
                "value": "Bragg",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "dcm-crystal_1_type": {
                "value": "silicon",
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
        },
    )
