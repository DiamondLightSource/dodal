import pytest
from ophyd_async.core import init_devices

from dodal.devices.temperture_controller.device_helper import (
    create_r_device_vector,
    create_rw_device_vector,
)


async def test_create_rw_device_vector():
    pv_index_offset = 1
    no_channels = 3
    async with init_devices(mock=True):
        lakeshore = create_rw_device_vector(
            prefix="888",
            no_channels=no_channels,
            write_pv="wpv",
            read_pv="rpv",
            signal_type=int,
            pv_index_offset=pv_index_offset,
            no_pv_suffix_index=False,
        )

    assert len(lakeshore) == no_channels

    for channel in lakeshore:
        assert lakeshore[channel].source[-1] == f"{channel + pv_index_offset}"


async def test_create_rw_device_vector_with_no_pv_index():
    pv_index_offset = 1
    no_channels = 1
    async with init_devices(mock=True):
        lakeshore = create_rw_device_vector(
            prefix="888",
            no_channels=no_channels,
            write_pv="wpv",
            read_pv="rpv",
            signal_type=int,
            pv_index_offset=pv_index_offset,
            no_pv_suffix_index=True,
        )

    assert len(lakeshore) == no_channels
    assert lakeshore[1].source.split("ca://")[-1] == "888rpv"


async def test_create_rw_device_vector_fail_multi_channel_with_no_pv_index():
    with pytest.raises(ValueError, match="Multi-channels require pv_suffix_index."):
        async with init_devices(mock=True):
            create_rw_device_vector(
                prefix="888",
                no_channels=4,
                write_pv="wpv",
                read_pv="rpv",
                signal_type=int,
                pv_index_offset=2,
                no_pv_suffix_index=True,
            )


async def test_create_r_device_vector():
    pv_index_offset = 1
    no_channels = 3
    async with init_devices(mock=True):
        lakeshore = create_r_device_vector(
            prefix="888",
            no_channels=no_channels,
            read_pv="rpv",
            signal_type=int,
            pv_index_offset=pv_index_offset,
            no_pv_suffix_index=False,
        )
    assert len(lakeshore) == no_channels

    for channel in lakeshore:
        assert lakeshore[channel].source[-1] == f"{channel + pv_index_offset}"


async def test_create_r_device_vector_with_no_pv_index():
    pv_index_offset = 1
    no_channels = 1
    async with init_devices(mock=True):
        lakeshore = create_r_device_vector(
            prefix="888",
            no_channels=no_channels,
            read_pv="rpv",
            signal_type=int,
            pv_index_offset=pv_index_offset,
            no_pv_suffix_index=True,
        )

    assert len(lakeshore) == no_channels
    assert lakeshore[1].source.split("ca://")[-1] == "888rpv"


async def test_create_r_device_vector_fail_multi_channel_with_no_pv_index():
    with pytest.raises(ValueError, match="Multi-channels require pv_suffix_index."):
        async with init_devices(mock=True):
            create_r_device_vector(
                prefix="888",
                no_channels=4,
                read_pv="rpv",
                signal_type=int,
                pv_index_offset=2,
                no_pv_suffix_index=True,
            )
