import pytest
from ophyd_async.core import init_devices

from dodal.beamlines.i03 import I03_ZEBRA_MAPPING
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    UnmappedZebraError,
    ZebraMapping,
    ZebraOutputs,
)


async def fake_zebra(zebra_mapping: ZebraMapping):
    async with init_devices(mock=True):
        zebra = Zebra(mapping=zebra_mapping, name="", prefix="")
    return zebra


async def test_exception_when_accessing_mapping_set_to_minus_1():
    mapping_no_output = ZebraMapping(outputs=ZebraOutputs())
    with pytest.raises(
        UnmappedZebraError,
        match="'ZebraOutputs.TTL_EIGER' was accessed but is set to -1. Please check the zebra mappings against the zebra's physical configuration",
    ):
        zebra = await fake_zebra(mapping_no_output)
        zebra.mapping.outputs.TTL_EIGER  # noqa: B018


def test_exception_when_multiple_fields_set_to_same_integer():
    expected_error_dict = {"TTL_DETECTOR": 1, "TTL_PANDA": 1}
    with pytest.raises(
        ValueError,
        match=f"must be mapped to a unique integer. Duplicate fields: {expected_error_dict}",
    ):
        ZebraMapping(outputs=ZebraOutputs(TTL_DETECTOR=1, TTL_PANDA=1))


async def test_validly_mapped_zebra_is_happy():
    zebra = await fake_zebra(zebra_mapping=I03_ZEBRA_MAPPING)
    assert zebra.mapping.outputs.TTL_DETECTOR == 1
    assert zebra.mapping.sources.DISCONNECT == 0
    assert zebra.mapping.AND_GATE_FOR_AUTO_SHUTTER == 2


async def test_setting_ttl_and_lvds_outputs_with_mapping_sets_expected_pvs():
    zebra = await fake_zebra(
        zebra_mapping=ZebraMapping(outputs=ZebraOutputs(TTL_SHUTTER=2, LVDS_EIGER=3))
    )
    await zebra.output.out_ttl_pvs[zebra.mapping.outputs.TTL_SHUTTER].set(
        zebra.mapping.sources.PC_PULSE
    )
    await zebra.output.out_lvds_pvs[zebra.mapping.outputs.LVDS_EIGER].set(
        zebra.mapping.sources.PC_GATE
    )

    out_ttl_2_pv = zebra.output.out_ttl_pvs[2]
    assert out_ttl_2_pv.name == "zebra-output-out_ttl_pvs-2"
    assert await out_ttl_2_pv.get_value() == 31

    out_lvds_3_pv = zebra.output.out_lvds_pvs[3]
    assert out_lvds_3_pv.name == "zebra-output-out_lvds_pvs-3"
    assert await out_lvds_3_pv.get_value() == 30
