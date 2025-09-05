import pytest
from ophyd_async.core import init_devices

from dodal.beamlines.i03 import I03_ZEBRA_MAPPING
from dodal.devices.zebra.zebra import Zebra
from dodal.devices.zebra.zebra_constants_mapping import (
    UnmappedZebraException,
    ZebraMapping,
    ZebraTTLOutputs,
)


async def fake_zebra(zebra_mapping: ZebraMapping):
    async with init_devices(mock=True):
        zebra = Zebra(mapping=zebra_mapping, name="", prefix="")
    return zebra


async def test_exception_when_accessing_mapping_set_to_minus_1():
    mapping_no_output = ZebraMapping(outputs=ZebraTTLOutputs())
    with pytest.raises(
        UnmappedZebraException,
        match="'ZebraTTLOutputs.TTL_EIGER' was accessed but is set to -1. Please check the zebra mappings against the zebra's physical configuration",
    ):
        zebra = await fake_zebra(mapping_no_output)
        zebra.mapping.outputs.TTL_EIGER  # noqa: B018


def test_exception_when_multiple_fields_set_to_same_integer():
    expected_error_dict = {"TTL_DETECTOR": 1, "TTL_PANDA": 1}
    with pytest.raises(
        ValueError,
        match=f"must be mapped to a unique integer. Duplicate fields: {expected_error_dict}",
    ):
        ZebraMapping(outputs=ZebraTTLOutputs(TTL_DETECTOR=1, TTL_PANDA=1))


async def test_validly_mapped_zebra_is_happy():
    zebra = await fake_zebra(zebra_mapping=I03_ZEBRA_MAPPING)
    assert zebra.mapping.outputs.TTL_DETECTOR == 1
    assert zebra.mapping.sources.DISCONNECT == 0
    assert zebra.mapping.AND_GATE_FOR_AUTO_SHUTTER == 2
