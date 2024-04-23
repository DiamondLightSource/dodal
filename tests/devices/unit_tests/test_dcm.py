from unittest.mock import ANY

import pytest
from ophyd.sim import make_fake_device
from ophyd_async.core import DeviceCollector

from dodal.beamlines.beamline_utils import device_instantiation
from dodal.devices.dcm import DCM

from ...conftest import MOCK_DAQ_CONFIG_PATH


@pytest.fixture
async def dcm() -> DCM:
    async with DeviceCollector(sim=True):
        dcm = DCM(
            "MY-DCM",
            name="dcm",
            daq_configuration_path=MOCK_DAQ_CONFIG_PATH,
        )
    return dcm


@pytest.fixture
async def staged_dcm(dcm: DCM):
    await dcm.stage()
    yield dcm
    await dcm.unstage()


def test_fixed_offset_lookup(dcm: DCM):
    assert dcm.fixed_offset_mm == 25.6


def test_lookup_paths_are_correct(dcm: DCM):
    assert (
        dcm.dcm_pitch_converter_lookup_table_path
        == MOCK_DAQ_CONFIG_PATH + "/lookup/BeamLineEnergy_DCM_Pitch_converter.txt"
    )
    assert (
        dcm.dcm_roll_converter_lookup_table_path
        == MOCK_DAQ_CONFIG_PATH + "/lookup/BeamLineEnergy_DCM_Roll_converter.txt"
    )


def test_energy_in_kev_not_hinted(dcm: DCM):
    assert "energy_in_kev" not in dcm.hints


async def test_dcm_describe_holds_describe_fields(staged_dcm: DCM):
    assert (await staged_dcm.describe()) == {
        "dcm-backplate_temp": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:TEMP5",
        },
        "dcm-bragg_in_degrees": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:BRAGG.RBV",
        },
        "dcm-energy_in_kev": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:ENERGY.RBV",
        },
        "dcm-offset_in_mm": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:OFFSET.RBV",
        },
        "dcm-perp_in_mm": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:PERP.RBV",
        },
        "dcm-perp_sub_assembly_temp": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:TEMP7",
        },
        "dcm-perp_temp": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:TEMP6",
        },
        "dcm-pitch_in_mrad": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:PITCH.RBV",
        },
        "dcm-roll_in_mrad": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:ROLL.RBV",
        },
        "dcm-wavelength": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:WAVELENGTH.RBV",
        },
        "dcm-xtal1_heater_temp": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:TEMP3",
        },
        "dcm-xtal1_temp": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:TEMP1",
        },
        "dcm-xtal2_heater_temp": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:TEMP4",
        },
        "dcm-xtal2_temp": {
            "dtype": "number",
            "shape": [],
            "source": "sim://MY-DCM-MO-DCM-01:TEMP2",
        },
    }


async def test_dcm_read_holds_read_fields(staged_dcm: DCM):
    assert (await staged_dcm.read()) == {
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
        "dcm-perp_in_mm": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "dcm-perp_sub_assembly_temp": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "dcm-perp_temp": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "dcm-pitch_in_mrad": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "dcm-roll_in_mrad": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "dcm-wavelength": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "dcm-xtal1_heater_temp": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "dcm-xtal1_temp": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "dcm-xtal2_heater_temp": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "dcm-xtal2_temp": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
    }
