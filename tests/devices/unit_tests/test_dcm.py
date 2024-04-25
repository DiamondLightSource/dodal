from typing import AsyncIterable

import pytest
from ophyd_async.core import (
    DeviceCollector,
)

from dodal.devices.dcm import DCM
from tests.conftest import MOCK_DAQ_CONFIG_PATH


@pytest.fixture
async def dcm() -> DCM:
    async with DeviceCollector(sim=True):
        dcm = DCM("DCM-01", name="dcm", daq_configuration_path=MOCK_DAQ_CONFIG_PATH)
    return dcm


def test_lookup_table_paths_passed(dcm: DCM):
    assert (
        dcm.dcm_pitch_converter_lookup_table_path
        == MOCK_DAQ_CONFIG_PATH + "/lookup/BeamLineEnergy_DCM_Pitch_converter.txt"
    )
    assert (
        dcm.dcm_roll_converter_lookup_table_path
        == MOCK_DAQ_CONFIG_PATH + "/lookup/BeamLineEnergy_DCM_Roll_converter.txt"
    )


async def test_offset_decoded(dcm: DCM):
    assert dcm.fixed_offset_mm == 25.6


@pytest.mark.parametrize(
    "key",
    [
        "dcm-backplate_temp",
        "dcm-bragg_in_degrees",
        "dcm-energy_in_kev",
        "dcm-offset_in_mm",
    ],
)
async def test_read_and_describe_includes(
    dcm: DCM,
    key: str,
):
    description = await dcm.describe()
    reading = await dcm.read()

    assert key in description
    assert key in reading
