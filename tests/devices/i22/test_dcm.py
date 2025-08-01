import bluesky.plans as bp
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_configuration,
    assert_emitted,
    assert_reading,
    partial_reading,
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


async def test_reading(dcm: DCM):
    await assert_reading(
        dcm,
        {
            "dcm-backplate_temp": partial_reading(0.0),
            "dcm-bragg_in_degrees": partial_reading(0.0),
            "dcm-crystal_1_heater_temp": partial_reading(0.0),
            "dcm-crystal_1_temp": partial_reading(0.0),
            "dcm-crystal_2_heater_temp": partial_reading(0.0),
            "dcm-crystal_2_temp": partial_reading(0.0),
            "dcm-crystal_metadata_d_spacing_a": partial_reading(0.0),
            "dcm-energy_in_kev": partial_reading(0.0),
            "dcm-offset_in_mm": partial_reading(0.0),
            "dcm-perp": partial_reading(0.0),
            "dcm-perp_temp": partial_reading(0.0),
            "dcm-wavelength_in_a": partial_reading(0.0),
            "dcm-xtal_1-roll_in_mrad": partial_reading(0.0),
            "dcm-xtal_2-pitch_in_mrad": partial_reading(0.0),
            "dcm-xtal_2-roll_in_mrad": partial_reading(0.0),
        },
    )


async def test_configuration(dcm: DCM):
    await assert_configuration(
        dcm,
        {
            "dcm-bragg_in_degrees-motor_egu": partial_reading(""),
            "dcm-bragg_in_degrees-offset": partial_reading(0.0),
            "dcm-bragg_in_degrees-velocity": partial_reading(0.0),
            "dcm-crystal_1_d_spacing": partial_reading(0.31356),
            "dcm-crystal_1_reflection": partial_reading([1, 1, 1]),
            "dcm-crystal_1_type": partial_reading("silicon"),
            "dcm-crystal_1_usage": partial_reading("Bragg"),
            "dcm-crystal_2_d_spacing": partial_reading(0.31356),
            "dcm-crystal_2_reflection": partial_reading([1, 1, 1]),
            "dcm-crystal_2_type": partial_reading("silicon"),
            "dcm-crystal_2_usage": partial_reading("Bragg"),
            "dcm-energy_in_kev-motor_egu": partial_reading(""),
            "dcm-energy_in_kev-offset": partial_reading(0.0),
            "dcm-energy_in_kev-velocity": partial_reading(0.0),
            "dcm-offset_in_mm-motor_egu": partial_reading(""),
            "dcm-offset_in_mm-offset": partial_reading(0.0),
            "dcm-offset_in_mm-velocity": partial_reading(0.0),
            "dcm-perp-motor_egu": partial_reading(""),
            "dcm-perp-offset": partial_reading(0.0),
            "dcm-perp-velocity": partial_reading(0.0),
            "dcm-wavelength_in_a-motor_egu": partial_reading(""),
            "dcm-wavelength_in_a-offset": partial_reading(0.0),
            "dcm-wavelength_in_a-velocity": partial_reading(0.0),
            "dcm-xtal_1-roll_in_mrad-motor_egu": partial_reading(""),
            "dcm-xtal_1-roll_in_mrad-offset": partial_reading(0.0),
            "dcm-xtal_1-roll_in_mrad-velocity": partial_reading(0.0),
            "dcm-xtal_2-pitch_in_mrad-motor_egu": partial_reading(""),
            "dcm-xtal_2-pitch_in_mrad-offset": partial_reading(0.0),
            "dcm-xtal_2-pitch_in_mrad-velocity": partial_reading(0.0),
            "dcm-xtal_2-roll_in_mrad-motor_egu": partial_reading(""),
            "dcm-xtal_2-roll_in_mrad-offset": partial_reading(0.0),
            "dcm-xtal_2-roll_in_mrad-velocity": partial_reading(0.0),
        },
    )
