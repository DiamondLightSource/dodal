import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.electron_analyser.mbs import (
    EntranceSlitInformation,
    EntranceSlitInformationDevice,
    SlitPosition,
)


@pytest.mark.parametrize("slit_pos", [pos.value for pos in SlitPosition])
def test_entrance_slit_info_to_slit_position(slit_pos: SlitPosition):
    slit_info = EntranceSlitInformation.from_slit_positions(slit_pos)
    assert slit_info.to_slit_position() == slit_pos


def test_entrance_slit_info_from_slit_position():
    slit_info = EntranceSlitInformation.from_slit_positions(
        SlitPosition.S010_A19_STRAIGHT
    )
    assert slit_info.size == 0.1
    assert slit_info.aperture == 1.9
    assert slit_info.shape == "Straight"
    assert slit_info.direction == "Vertical"

    slit_info = EntranceSlitInformation.from_slit_positions(
        SlitPosition.S020_A10_CURVED
    )
    assert slit_info.size == 0.2
    assert slit_info.aperture == 1.0
    assert slit_info.shape == "Curved"
    assert slit_info.direction == "Vertical"


@pytest.fixture
def slit_info_device() -> EntranceSlitInformationDevice:
    with init_devices(mock=True):
        slit_info_device = EntranceSlitInformationDevice("TEST:")
    return slit_info_device


@pytest.mark.parametrize("slit_pos", [pos.value for pos in SlitPosition])
async def test_slit_info_device_soft_signals_sync_with_epics(
    slit_info_device: EntranceSlitInformationDevice, slit_pos: SlitPosition
) -> None:
    await slit_info_device.set(slit_pos)

    slit_info = EntranceSlitInformation.from_slit_positions(slit_pos)
    assert await slit_info_device.aperture.get_value() == slit_info.aperture
    assert await slit_info_device.shape.get_value() == slit_info.shape
    assert await slit_info_device.size.get_value() == slit_info.size
    assert await slit_info_device.direction.get_value() == slit_info.direction


@pytest.mark.parametrize("slit_pos", [pos.value for pos in SlitPosition])
async def test_slit_info_device_read_and_soft_signals_sync_with_epics(
    slit_info_device: EntranceSlitInformationDevice, slit_pos: SlitPosition
) -> None:
    await slit_info_device.set(slit_pos)
    slit_info = EntranceSlitInformation.from_slit_positions(slit_pos)

    await assert_reading(
        slit_info_device,
        {
            "slit_info_device-size": partial_reading(slit_info.size),
            "slit_info_device-shape": partial_reading(slit_info.shape),
            "slit_info_device-aperture": partial_reading(slit_info.aperture),
            "slit_info_device-direction": partial_reading(slit_info.direction),
        },
    )


async def test_slit_info_device_multiple_connects_has_one_subscribe(
    slit_info_device: EntranceSlitInformationDevice,
):
    expected_subscribers = 1
    number_of_subscribers = len(slit_info_device.slit_pos._get_cache()._listeners)
    assert number_of_subscribers == expected_subscribers
    # Test if we connect again if another subscriber is added, checking for memory leaks.
    for _ in range(3):
        await slit_info_device.connect(mock=True)
        assert (
            len(slit_info_device.slit_pos._get_cache()._listeners)
            == expected_subscribers
        )
