import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.oav.beam_centre.centroid_from_epics import CentroidFromEpics


@pytest.fixture
def centroid_device() -> CentroidFromEpics:
    with init_devices(mock=True):
        device = CentroidFromEpics("", name="mock_centroid")
    set_mock_value(device.beam_centre_x, 706)
    set_mock_value(device.beam_centre_y, 283)
    return device


async def test_set_plugin_chain(centroid_device: CentroidFromEpics):
    await centroid_device.cc_array_port.set("OAV1.cam")
    await centroid_device.stat_array_port.set("OAV1.cc")

    assert await centroid_device.stat_array_port.get_value() == "OAV1.cc"
    assert await centroid_device.cc_array_port.get_value() == "OAV1.cam"


async def test_centroid_can_be_read(centroid_device: CentroidFromEpics):
    await assert_reading(
        centroid_device,
        {
            "mock_centroid-beam_centre_x": partial_reading(706),
            "mock_centroid-beam_centre_y": partial_reading(18),
        },
    )
