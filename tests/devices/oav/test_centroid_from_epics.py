import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.oav.beam_centre.centroid_from_epics import (
    CentroidFromEpics,
    CentroidSettings,
    ColourMode,
)


@pytest.fixture
async def centroid_device() -> CentroidFromEpics:
    with init_devices(mock=True):
        device = CentroidFromEpics("", name="mock_centroid")
    set_mock_value(device.beam_centre_x, 706)
    set_mock_value(device.beam_centre_y, 283)
    return device


@pytest.mark.parametrize(
    "threshold, colour_mode", [(20, ColourMode.MONO), (10, ColourMode.RGB1)]
)
async def test_prepare_sets_the_plugin_chain(
    threshold: float,
    colour_mode: ColourMode,
    centroid_device: CentroidFromEpics,
):
    await centroid_device.prepare(
        CentroidSettings(threshold=threshold, colour_mode=colour_mode)
    )

    assert await centroid_device.stat_array_port.get_value() == "OAV1.cc"
    assert await centroid_device.cc_array_port.get_value() == "OAV1.cam"
    assert await centroid_device.centroid_threshold.get_value() == threshold
    assert await centroid_device.colour_mode.get_value() == colour_mode.value


async def test_centroid_position_can_be_read(centroid_device: CentroidFromEpics):
    await assert_reading(
        centroid_device,
        {
            "mock_centroid-beam_centre_x": partial_reading(706),
            "mock_centroid-beam_centre_y": partial_reading(283),
        },
        False,
    )
