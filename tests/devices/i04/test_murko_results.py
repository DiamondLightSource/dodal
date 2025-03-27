import asyncio
import json
import pickle
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ophyd_async.core import (
    init_devices,
    wait_for_value,
)
from ophyd_async.testing import set_mock_value

from dodal.devices.i04.murko_results import MurkoResultsDevice


@pytest.fixture
# @patch("dodal.devices.i04.murko_results.soft_signal_rw")
@patch("dodal.devices.i04.murko_results.StrictRedis")
async def fake_murko_results(fake_strict_redis) -> MurkoResultsDevice:
    murko_results = MurkoResultsDevice(prefix="", name="murko_results")
    return murko_results


@pytest.fixture
async def fake_setters(
    fake_murko_results: MurkoResultsDevice,
) -> tuple[MagicMock, MagicMock, MagicMock]:
    mock_x_setter = MagicMock()
    mock_y_setter = MagicMock()
    mock_z_setter = MagicMock()
    fake_murko_results._x_um_setter = mock_x_setter
    fake_murko_results._y_um_setter = mock_y_setter
    fake_murko_results._z_um_setter = mock_z_setter
    return mock_x_setter, mock_y_setter, mock_z_setter


def pickled_messages(messages) -> list:
    for message in messages:
        message["data"] = pickle.dumps(message["data"])
    messages.append(None)
    return messages


def get_messages(
    batches: int = 2,
    messages_per_batch: int = 1,
    images_per_message: int = 1,
    start_x: float = 0.5,
    start_y: float = 0.5,
    step_x: float = 0,
    step_y: float = 0,
    shape: tuple[int, int] = (100, 100),
) -> list:
    messages = []
    uuid = 0
    for _ in range(batches):
        data = []
        for _ in range(messages_per_batch):
            data_point = {}
            for _ in range(images_per_message):
                data_point[uuid] = {
                    "most_likely_click": (
                        start_x + step_x * uuid,
                        start_y + step_y * uuid,
                    ),
                    "original_shape": shape,
                }
                uuid += 1
            data.append(data_point)
        messages.append({"type": "message", "data": data})
    return messages


def json_metadata(n, start=90, step=1, microns_pxp=10, microns_pyp=10) -> dict:
    metadatas = {}
    for i in range(n):
        metadata = {
            "omega_angle": start + step * i,
            "microns_per_x_pixel": microns_pxp,
            "microns_per_y_pixel": microns_pyp,
        }
        metadatas[i] = json.dumps(metadata)
    return metadatas


# @patch("dodal.devices.i04.murko_results.StrictRedis")
# async def test_complete_calls_get_message_and_hget(
#     fake_strict_redis,
#     fake_murko_results,
# ):
#     messages = iter(pickled_messages(get_messages()))
#     metadata = iter(json_metadata(2, start=90, step=90))
#     with (
#         patch.object(
#             fake_strict_redis.pubsub,
#             "get_message",
#             new_callable=AsyncMock,
#             side_effect=lambda *args, **kwargs: next(messages),
#         ) as mock_get_message,
#         patch.object(
#             fake_strict_redis,
#             "hget",
#             new_callable=AsyncMock,
#             side_effect=lambda *args, **kwargs: next(metadata),
#         ) as mock_hget,
#     ):
#         fake_murko_results.pubsub.get_message = mock_get_message
#         fake_murko_results.redis_client.hget = mock_hget
#         await fake_murko_results.trigger()
#         assert fake_murko_results.pubsub.get_message.call_count == 6
#     assert fake_murko_results.redis_client.hget.call_count == 100


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_no_movement_given_sample_centre_matches_beam_centre(
    fake_strict_redis, fake_murko_results, fake_setters
):
    mock_x_setter, mock_y_setter, mock_z_setter = fake_setters
    messages = iter(pickled_messages(get_messages()))  # 2 messages, both (0.5, 0.5)
    metadata = json_metadata(2, start=90, step=90)  # at exactly 90, 180 degrees
    with (
        patch.object(
            fake_strict_redis.pubsub,
            "get_message",
            new_callable=AsyncMock,
            side_effect=lambda *args, **kwargs: next(messages),
        ) as mock_get_message,
        patch.object(
            fake_strict_redis,
            "hget",
            new_callable=AsyncMock,
            side_effect=lambda blah, uuid: metadata[uuid],
        ) as mock_hget,
        patch.object(
            fake_murko_results,
            "get_beam_centre",
            side_effect=lambda *args, **kwargs: (50, 50),
        ) as mock_get_beam_centre,
    ):
        fake_murko_results.pubsub.get_message = mock_get_message
        fake_murko_results.redis_client.hget = mock_hget
        fake_murko_results.get_beam_centre = mock_get_beam_centre
        await fake_murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == 0
    assert mock_y_setter.call_args[0][0] == 0
    assert mock_z_setter.call_args[0][0] == 0


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_given_correct_movement_given_90_and_180_angles(  # Need a better name
    fake_strict_redis, fake_murko_results, fake_setters
):
    mock_x_setter, mock_y_setter, mock_z_setter = fake_setters
    messages = iter(pickled_messages(get_messages()))  # 2 messages, both (0.5, 0.5)
    metadata = json_metadata(2, start=90, step=90)  # at exactly 90, 180 degrees
    with (
        patch.object(
            fake_strict_redis.pubsub,
            "get_message",
            new_callable=AsyncMock,
            side_effect=lambda *args, **kwargs: next(messages),
        ) as mock_get_message,
        patch.object(
            fake_strict_redis,
            "hget",
            new_callable=AsyncMock,
            side_effect=lambda blah, uuid: metadata[uuid],
        ) as mock_hget,
        patch.object(
            fake_murko_results,
            "get_beam_centre",
            side_effect=lambda *args, **kwargs: (75, 70),
        ) as mock_get_beam_centre,
    ):
        fake_murko_results.pubsub.get_message = mock_get_message
        fake_murko_results.redis_client.hget = mock_hget
        fake_murko_results.get_beam_centre = mock_get_beam_centre
        await fake_murko_results.trigger()
    # (sample_centre_x * shape[0] - beam_centre_x) / microns_pxp -> (0.5 * 100 - 75) / 10
    assert mock_x_setter.call_args[0][0] == -0.25
    # (sample_centre_y * shape[1] - beam_centre_y) / microns_pyp -> (0.5 * 100 - 70) / 10
    assert mock_y_setter.call_args[0][0] == 0.2
    # (sample_centre_z * shape[1] - beam_centre_y) / microns_pyp -> (0.5 * 100 - 70) / 10
    assert mock_z_setter.call_args[0][0] == 0.2


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_given_correct_movement_given_30_and_210_angles(  # Need a better name
    fake_strict_redis, fake_murko_results, fake_setters
):
    mock_x_setter, mock_y_setter, mock_z_setter = fake_setters
    messages = iter(pickled_messages(get_messages()))  # 2 messages, both (0.5, 0.5)
    metadata = json_metadata(2, start=30, step=190)  # at exactly 90, 180 degrees
    with (
        patch.object(
            fake_strict_redis.pubsub,
            "get_message",
            new_callable=AsyncMock,
            side_effect=lambda *args, **kwargs: next(messages),
        ) as mock_get_message,
        patch.object(
            fake_strict_redis,
            "hget",
            new_callable=AsyncMock,
            side_effect=lambda blah, uuid: metadata[uuid],
        ) as mock_hget,
        patch.object(
            fake_murko_results,
            "get_beam_centre",
            side_effect=lambda *args, **kwargs: (75, 70),
        ) as mock_get_beam_centre,
    ):
        fake_murko_results.pubsub.get_message = mock_get_message
        fake_murko_results.redis_client.hget = mock_hget
        fake_murko_results.get_beam_centre = mock_get_beam_centre
        await fake_murko_results.trigger()
    # (sample_centre_x * shape[0] - beam_centre_x) / microns_pxp -> (0.5 * 100 - 75) / 10
    assert mock_x_setter.call_args[0][0] == -0.25
    # (sample_centre_y * shape[1] - beam_centre_y) / microns_pyp -> (0.5 * 100 - 70) / 10
    assert mock_y_setter.call_args[0][0] == 0.2
    # (sample_centre_z * shape[1] - beam_centre_y) / microns_pyp -> (0.5 * 100 - 70) / 10
    assert mock_z_setter.call_args[0][0] == 0.2


# async def test_complete_ends_once_last_search_angle_is_found(fake_murko_results):
#     fake_murko_results.angles_to_search = fake_murko_results.angles_to_search[:-1]
#     await fake_murko_results.trigger()
#     assert fake_murko_results.pubsub.get_message.call_count == 4
#     assert fake_murko_results.redis_client.hget.call_count == 80


# async def test_complete_xyz_set_value(fake_murko_results, fake_setters):
#     mock_x_setter, mock_y_setter, mock_z_setter = fake_setters
#     await fake_murko_results.trigger()
#     assert mock_x_setter.call_args[0][0] == 10
