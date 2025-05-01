import json
import pickle
from collections.abc import Iterable
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from pytest import approx

from dodal.devices.i04.murko_results import MurkoResultsDevice
from dodal.devices.oav.oav_calculations import camera_coordinates_to_xyz_mm


@pytest.fixture
@patch("dodal.devices.i04.murko_results.StrictRedis")
async def mock_murko_results(mock_strict_redis) -> MurkoResultsDevice:
    murko_results = MurkoResultsDevice(name="murko_results")
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


def get_y_after_rotation(theta, y, z, beam_centre_y, shape_y):
    cos_a = np.cos(np.radians(theta))
    sin_a = np.sin(np.radians(theta))
    rel_y = y - beam_centre_y / shape_y
    new_y = cos_a * rel_y - sin_a * z + beam_centre_y / shape_y
    return new_y


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
    xyz: tuple[float, float, float] = (0.5, 0.5, 0.0),
    omega_start: float = 90,
    omega_step: float = 90,
    beam_centre_i: int = 50,
    beam_centre_j: int = 50,
    shape_x: int = 100,
    shape_y: int = 100,
    microns_pxp: float = 10,
    microns_pyp: float = 10,
    x_drift: float = 0,
) -> tuple[Iterable, dict]:
    """Generate mock Murko messages and metadata with accurate most_likely_click values,
    based on x, y, z and a range of omega values. By default, xyz lines up with the beam
    centre."""
    messages = []
    uuid = 0
    omega = omega_start
    x, y, z = xyz
    for _ in range(batches):
        data = []
        for _ in range(messages_per_batch):
            data_point = {}
            for _ in range(images_per_message):
                data_point[uuid] = {
                    "most_likely_click": (
                        get_y_after_rotation(omega, y, z, beam_centre_j, shape_y),
                        x + x_drift * uuid,  # Murko returns coords as y, x
                    ),
                    "original_shape": (shape_y, shape_x),  # (y, x) to match Murko
                }
                uuid += 1
                omega += omega_step
            data.append(data_point)
        messages.append({"type": "message", "data": data})
    metadata = json_metadata(
        n=batches * messages_per_batch * images_per_message,
        start=omega_start,
        step=omega_step,
        microns_pxp=microns_pxp,
        microns_pyp=microns_pyp,
        beam_centre_i=beam_centre_i,
        beam_centre_j=beam_centre_j,
    )
    return iter(pickled_messages(messages)), metadata


def json_metadata(
    n: int,
    start: float = 90,
    step: float = 1,
    microns_pxp: float = 10,
    microns_pyp: float = 10,
    beam_centre_i: int = 50,
    beam_centre_j: int = 50,
) -> dict:
    metadatas = {}
    for i in range(n):
        metadata = {
            "omega_angle": start + step * i,
            "microns_per_x_pixel": microns_pxp,
            "microns_per_y_pixel": microns_pyp,
            "beam_centre_i": beam_centre_i,
            "beam_centre_j": beam_centre_j,
        }
        metadatas[i] = json.dumps(metadata)
    return metadatas


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_no_movement_given_sample_centre_matches_beam_centre(
    mock_strict_redis, mock_murko_results, mock_setters
):
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        images_per_message=10, omega_start=50, omega_step=5
    )  # Crystal alligned with beam centre
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await mock_murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == 0, "wrong x"
    assert mock_y_setter.call_args[0][0] == 0, "wrong y"
    assert mock_z_setter.call_args[0][0] == 0, "wrong z"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_given_correct_movement_given_90_and_180_angles_with_0_z(
    mock_strict_redis, mock_murko_results, mock_setters
):
    x = 0.5
    y = 0.4
    z = 0
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        xyz=(x, y, z), beam_centre_i=75, beam_centre_j=70
    )  # 2 messages
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await mock_murko_results.trigger()

    expected_x = x - 0.75  # beam_centre_i / shape_x = 0.75
    assert mock_x_setter.call_args[0][0] == expected_x, "wrong x"

    expected_y = y - 0.7  # beam_centre_j / shape_y = 0.7
    assert mock_y_setter.call_args[0][0] == approx(expected_y), "wrong y"

    expected_z = z
    assert mock_z_setter.call_args[0][0] == approx(expected_z), "wrong z"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_90_180_degrees(
    mock_strict_redis, mock_murko_results, mock_setters
):
    x = 0.5
    y = 0.6
    z = 0.3
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        xyz=(x, y, z), beam_centre_i=90, beam_centre_j=40, shape_x=100, shape_y=100
    )
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await mock_murko_results.trigger()

    assert mock_x_setter.call_args[0][0] == x - 0.9, "wrong x"
    assert mock_y_setter.call_args[0][0] == approx(y - 0.4), "wrong y"
    assert mock_z_setter.call_args[0][0] == approx(z), "wrong z"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_45_and_135_angles(
    mock_strict_redis, mock_murko_results, mock_setters
):
    x = 0.5
    y = 0.3
    z = 0.4
    xyz = x, y, z
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        xyz=xyz, omega_start=45, omega_step=90, beam_centre_i=75, beam_centre_j=70
    )
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await mock_murko_results.trigger()

    assert mock_x_setter.call_args[0][0] == x - 0.75, "wrong x"
    assert mock_y_setter.call_args[0][0] == approx(y - 0.7), "wrong y"
    assert mock_z_setter.call_args[0][0] == approx(z), "wrong z"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_30_and_120_angles(
    mock_strict_redis, mock_murko_results, mock_setters
):
    x = 1
    y = 1
    z = 1
    xyz = (x, y, z)
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        xyz=xyz, omega_start=30, omega_step=90, beam_centre_i=75, beam_centre_j=70
    )
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await mock_murko_results.trigger()

    assert mock_x_setter.call_args[0][0] == x - 0.75, "wrong x"
    assert mock_y_setter.call_args[0][0] == approx(y - 0.7), "wrong y"
    assert mock_z_setter.call_args[0][0] == approx(z), "wrong z"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_30_and_150_angles_with_x_drift(
    mock_strict_redis, mock_murko_results, mock_setters
):
    x = 1
    y = 1
    z = 1
    xyz = (x, y, z)
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        xyz=xyz,
        omega_start=30,
        omega_step=120,
        beam_centre_i=75,
        beam_centre_j=70,
        x_drift=0.1,
    )
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await mock_murko_results.trigger()

    assert mock_x_setter.call_args[0][0] == np.mean([x, x + 0.1]) - 0.75, "wrong x"
    assert mock_y_setter.call_args[0][0] == approx(y - 0.7), "wrong y"
    assert mock_z_setter.call_args[0][0] == approx(z), "wrong z"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_multiple_angles(
    mock_strict_redis, mock_murko_results, mock_setters
):
    x = 0.1
    y = 0.2
    z = 0.3
    xyz = (x, y, z)
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        batches=2,
        messages_per_batch=2,
        images_per_message=3,
        xyz=xyz,
        omega_start=22.4,
        omega_step=20.7,
        beam_centre_i=75,
        beam_centre_j=70,
    )
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await mock_murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == approx(x - 0.75), "wrong x"
    assert mock_y_setter.call_args[0][0] == approx(y - 0.7), "wrong y"
    assert mock_z_setter.call_args[0][0] == approx(z), "wrong z"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_multiple_angles_and_x_drift(
    mock_strict_redis, mock_murko_results, mock_setters
):
    x = 0.1
    y = 0.2
    z = 0.3
    xyz = (x, y, z)
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        batches=2,
        messages_per_batch=2,
        images_per_message=3,
        xyz=xyz,
        omega_start=22.4,
        omega_step=20.7,
        beam_centre_i=75,
        beam_centre_j=70,
        x_drift=0.01,
    )
    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await mock_murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == approx(x + 0.055 - 0.75), "wrong x"
    assert mock_y_setter.call_args[0][0] == approx(y - 0.7), "wrong y"
    assert mock_z_setter.call_args[0][0] == approx(z), "wrong z"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_trigger_calls_get_message_and_hget(
    mock_strict_redis,
    mock_murko_results,
):
    messages, metadata = get_messages(
        batches=4, messages_per_batch=3, images_per_message=2, omega_step=5
    )

    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await mock_murko_results.trigger()
    # 4 messages to find, plus one None message
    assert mock_murko_results.pubsub.get_message.call_count == 5
    # 4 * 3 * 2 metadata messages
    assert mock_murko_results.redis_client.hget.call_count == 24


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_trigger_stops_once_last_angle_found(
    mock_strict_redis,
    mock_murko_results,
):
    messages, metadata = get_messages(
        batches=5,
        messages_per_batch=3,
        images_per_message=2,
        omega_start=90,
        omega_step=10,
    )

    mock_murko_results.pubsub.get_message, mock_murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    mock_murko_results.stop_angle = 200
    await mock_murko_results.trigger()
    # Takes 2 batches to find the last angle, 200°
    assert mock_murko_results.pubsub.get_message.call_count == 2
    # 4 batches of 6 = 24
    assert mock_murko_results.redis_client.hget.call_count == 12
