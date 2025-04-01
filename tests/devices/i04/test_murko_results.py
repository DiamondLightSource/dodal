import json
import pickle
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from pytest import approx

from dodal.devices.i04.murko_results import MurkoResultsDevice
from dodal.devices.oav.oav_calculations import camera_coordinates_to_xyz_mm


@pytest.fixture
# @patch("dodal.devices.i04.murko_results.soft_signal_rw")
@patch("dodal.devices.i04.murko_results.StrictRedis")
async def mock_murko_results(mock_strict_redis) -> MurkoResultsDevice:
    murko_results = MurkoResultsDevice(prefix="", name="murko_results")
    return murko_results


@pytest.fixture
async def mock_setters(
    mock_murko_results: MurkoResultsDevice,
) -> tuple[MagicMock, MagicMock, MagicMock]:
    mock_x_setter = MagicMock()
    mock_y_setter = MagicMock()
    mock_z_setter = MagicMock()
    mock_murko_results._x_mm_setter = mock_x_setter
    mock_murko_results._y_mm_setter = mock_y_setter
    mock_murko_results._z_mm_setter = mock_z_setter
    return mock_x_setter, mock_y_setter, mock_z_setter


def mock_redis_calls(mock_strict_redis, messages, metadata):
    mock_get_message = patch.object(
        mock_strict_redis.pubsub,
        "get_message",
        new_callable=AsyncMock,
        side_effect=lambda *args, **kwargs: next(messages),
    ).start()
    mock_hget = patch.object(
        mock_strict_redis,
        "hget",
        new_callable=AsyncMock,
        side_effect=lambda _, uuid: metadata[uuid],
    ).start()
    return mock_get_message, mock_hget


def mock_get_beam_centre(mock_murko_results, x, y):
    return patch.object(
        mock_murko_results,
        "get_beam_centre",
        side_effect=lambda *args, **kwargs: (x, y),
    ).start()


def abs_cos(degrees):
    return abs(np.cos(np.radians(degrees)))


def abs_sin(degrees):
    return abs(np.sin(np.radians(degrees)))


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
    shape_x: int = 100,
    shape_y: int = 100,
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
                        start_y + step_y * uuid,  # Murko returns coords as y, x
                        start_x + step_x * uuid,
                    ),
                    "original_shape": (shape_y, shape_x),  # (y, x) to match Murko
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


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_no_movement_given_sample_centre_matches_beam_centre(
    mock_strict_redis, mock_murko_results, mock_setters
):
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages = iter(pickled_messages(get_messages()))  # 2 messages, both (0.5, 0.5)
    metadata = json_metadata(2, start=90, step=90)  # at exactly 90, 180 degrees
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    mock_murko_results.get_beam_centre = mock_get_beam_centre(
        mock_murko_results, 50, 50
    )
    await mock_murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == 0
    assert mock_y_setter.call_args[0][0] == 0
    assert mock_z_setter.call_args[0][0] == 0


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_given_correct_movement_given_90_and_180_angles(  # Need a better name
    mock_strict_redis, mock_murko_results, mock_setters
):
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages = iter(pickled_messages(get_messages()))  # 2 messages, both (0.5, 0.5)
    metadata = json_metadata(2, start=90, step=90)  # at exactly 90, 180 degrees
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    mock_murko_results.get_beam_centre = mock_get_beam_centre(
        mock_murko_results, 75, 70
    )
    await mock_murko_results.trigger()
    # (sample_centre_x * shape[1] - beam_centre_x) * microns_pxp / 1000 -> (0.5 * 100 - 75) / 100
    assert mock_x_setter.call_args[0][0] == -0.25
    # (sample_centre_y * shape[0] - beam_centre_y) * microns_pyp / 1000 -> (0.5 * 100 - 70) / 100
    assert mock_y_setter.call_args[0][0] == 0.2
    # (sample_centre_z * shape[0] - beam_centre_y) * microns_pyp / 1000 -> (0.5 * 100 - 70) / 100
    assert mock_z_setter.call_args[0][0] == 0.2


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_90_180_degrees(
    mock_strict_redis, mock_murko_results, mock_setters
):
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages = iter(
        pickled_messages(get_messages(start_y=0.6, step_y=0.1))
    )  # 2 messages, (0.6, 0.5) and (0.7, 0.5) - (z, x), (y, x)
    metadata = json_metadata(2, start=90, step=90)  # at 90, 180 degrees
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    mock_murko_results.get_beam_centre = mock_get_beam_centre(
        mock_murko_results, 90, 40
    )
    await mock_murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == -0.4  # - (0.9 - 0.5)
    assert mock_y_setter.call_args[0][0] == -0.3  # 0.4 - 0.7
    assert mock_z_setter.call_args[0][0] == -0.2  # 0.4 - 0.6


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_45_and_135_angles(
    mock_strict_redis, mock_murko_results, mock_setters
):
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages = iter(pickled_messages(get_messages()))  # 2 messages, both (0.5, 0.5)
    metadata = json_metadata(2, start=45, step=90)  # at 45, 135 degrees
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    mock_murko_results.get_beam_centre = mock_get_beam_centre(
        mock_murko_results, 75, 70
    )
    await mock_murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == -0.25
    expected_y = 0.2 * abs_cos(135)
    assert mock_y_setter.call_args[0][0] == approx(expected_y)
    expected_z = 0.2 * abs_sin(45)
    assert mock_z_setter.call_args[0][0] == approx(expected_z)


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_30_and_120_angles(
    mock_strict_redis, mock_murko_results, mock_setters
):
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages = iter(pickled_messages(get_messages()))  # 2 messages, both (0.5, 0.5)
    metadata = json_metadata(2, start=30, step=90)  # at 30, 120 degrees
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    mock_murko_results.get_beam_centre = mock_get_beam_centre(
        mock_murko_results, 75, 70
    )
    await mock_murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == -0.25, "x value incorrect"
    # (sample_centre_y * shape[1] - beam_centre_y) / microns_pyp -> (0.5 * 100 - 70) / 10
    expected_y = 0.2 * abs_cos(120)
    assert mock_y_setter.call_args[0][0] == approx(expected_y), "y value incorrect"
    # (sample_centre_z * shape[1] - beam_centre_y) / microns_pyp -> (0.5 * 100 - 70) / 10
    expected_z = 0.2 * abs_sin(120)  # closer than 30
    assert mock_z_setter.call_args[0][0] == approx(expected_z), "z value incorrect"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_30_and_150_angles(
    mock_strict_redis, mock_murko_results, mock_setters
):
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages = iter(pickled_messages(get_messages()))  # 2 messages, both (0.5, 0.5)
    metadata = json_metadata(2, start=30, step=120)  # at 30, 120 degrees
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    mock_murko_results.get_beam_centre = mock_get_beam_centre(
        mock_murko_results, 75, 70
    )
    await mock_murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == -0.25, "x value incorrect"
    # (sample_centre_y * shape[1] - beam_centre_y) / microns_pyp -> (0.5 * 100 - 70) / 10
    expected_y = 0.2 * abs_cos(150)
    assert mock_y_setter.call_args[0][0] == approx(expected_y), "y value incorrect"
    # (sample_centre_z * shape[1] - beam_centre_y) / microns_pyp -> (0.5 * 100 - 70) / 10
    expected_z = 0.2 * abs_sin(30)
    assert mock_z_setter.call_args[0][0] == approx(expected_z), "z value incorrect"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_multiple_angles(  # Need a better name
    mock_strict_redis, mock_murko_results, mock_setters
):
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages = iter(
        pickled_messages(get_messages(batches=7))
    )  # 2 messages, both (0.5, 0.5)
    metadata = json_metadata(7, start=20, step=30)  # Should find 80, 170 degrees
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    mock_murko_results.get_beam_centre = mock_get_beam_centre(
        mock_murko_results, 75, 60
    )
    await mock_murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == -0.25, "x value incorrect"
    # (60 - 0.5 * 100) * 10 / 1000 = 0.1
    expected_y = 0.1 * abs_cos(170)  # 170 is closest angle to 180
    assert mock_y_setter.call_args[0][0] == approx(expected_y), "y value incorrect"
    expected_z = 0.1 * abs_sin(80)  # 80 is closest angle to 90
    assert mock_z_setter.call_args[0][0] == approx(expected_z), "z value incorrect"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_multiple_angles_and_shifting_coords(
    mock_strict_redis, mock_murko_results, mock_setters
):
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages = iter(
        pickled_messages(
            get_messages(
                batches=3,
                messages_per_batch=2,
                images_per_message=2,
                start_x=0.5,
                step_x=0.01,
                start_y=0.3,
                step_y=0.02,
            )
        )
    )  # 2 messages, both (0.5, 0.5)
    metadata = json_metadata(12, start=75, step=10)  # Should find 85, 175 degrees
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    mock_murko_results.get_beam_centre = mock_get_beam_centre(
        mock_murko_results, 75, 60
    )
    await mock_murko_results.trigger()
    # at 85, 175, x_coord = 0.51, 0.6. Average = 0.555. Beam_centre_x = 75. 0.75 - 0.555 = 0.195
    assert mock_x_setter.call_args[0][0] == -0.195, "x value incorrect"
    # at 175, y_coord = 0.5. 0.6 - 0.5 = 0.1
    expected_y = 0.1 * abs_cos(175)  # 175 is closest angle to 180
    assert mock_y_setter.call_args[0][0] == approx(expected_y), "y value incorrect"
    # at 85, y_coord = 0.32. 0.6 - 0.32 = 0.28.
    expected_z = 0.28 * abs_sin(85)  # 85 is closest angle to 90
    assert mock_z_setter.call_args[0][0] == approx(expected_z), "z value incorrect"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_trigger_calls_get_message_and_hget(
    mock_strict_redis,
    mock_murko_results,
):
    messages = iter(
        pickled_messages(
            get_messages(
                batches=4,
                messages_per_batch=3,
                images_per_message=2,
            )
        )
    )
    metadata = json_metadata(24, start=80, step=5)  # 24 scans 5° apart
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await mock_murko_results.trigger()
    assert mock_murko_results.pubsub.get_message.call_count == 5
    # last batch is run twice, 4 * 6 + 6
    assert mock_murko_results.redis_client.hget.call_count == 30


@patch(
    "dodal.devices.i04.murko_results.camera_coordinates_to_xyz_mm",
    wraps=camera_coordinates_to_xyz_mm,
)
@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_trigger_stops_once_last_angle_found(
    mock_strict_redis,
    mock_camera_coordinates,
    mock_murko_results,
):
    messages = iter(
        pickled_messages(
            get_messages(
                batches=5,
                messages_per_batch=3,
                images_per_message=2,
            )
        )
    )
    metadata = json_metadata(30, start=70, step=10)  # 30 scans 10° apart
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await mock_murko_results.trigger()
    # Takes 4 batches to find the last angle, 270°
    assert mock_murko_results.pubsub.get_message.call_count == 4
    # 4 batches of 6 = 24
    assert mock_murko_results.redis_client.hget.call_count == 24
    assert mock_camera_coordinates.call_count == 3  # Should be called for 90, 180, 270
    assert mock_camera_coordinates.call_args_list[0][0][2] == 90
    assert mock_camera_coordinates.call_args_list[1][0][2] == 180
    assert mock_camera_coordinates.call_args_list[2][0][2] == 270
