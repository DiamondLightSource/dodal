import json
import pickle
from collections.abc import Iterable
from typing import cast
from unittest.mock import AsyncMock, MagicMock, call, patch

import numpy as np
import pytest
from pytest import approx

from dodal.devices.i04.murko_results import (
    MurkoMetadata,
    MurkoResultsDevice,
    get_yz_least_squares,
)


@pytest.fixture
@patch("dodal.devices.i04.murko_results.StrictRedis")
async def murko_results(mock_strict_redis: MagicMock) -> MurkoResultsDevice:
    murko_results = MurkoResultsDevice(name="murko_results")
    return murko_results


@pytest.fixture
async def mock_setters(
    murko_results: MurkoResultsDevice,
) -> tuple[MagicMock, MagicMock, MagicMock]:
    mock_x_setter = MagicMock()
    mock_y_setter = MagicMock()
    mock_z_setter = MagicMock()
    murko_results._x_mm_setter = mock_x_setter
    murko_results._y_mm_setter = mock_y_setter
    murko_results._z_mm_setter = mock_z_setter
    return mock_x_setter, mock_y_setter, mock_z_setter


def mock_redis_calls(mock_strict_redis: MagicMock, messages, metadata):
    mock_get_message = (
        patch.object(
            mock_strict_redis.pubsub,
            "get_message",
            new_callable=AsyncMock,
            side_effect=lambda *args, **kwargs: next(messages),
        ).start()
        if messages
        else None
    )
    mock_hget = (
        patch.object(
            mock_strict_redis,
            "hget",
            new_callable=AsyncMock,
            side_effect=lambda _, uuid: metadata[uuid],
        ).start()
        if metadata
        else None
    )
    return mock_get_message, mock_hget


def mock_get_beam_centre(murko_results, x, y):
    return patch.object(
        murko_results,
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
        batch = []
        for _ in range(messages_per_batch):
            results = {}
            for _ in range(images_per_message):
                results[uuid] = {
                    "most_likely_click": (
                        get_y_after_rotation(omega, y, z, beam_centre_j, shape_y),
                        x + x_drift * uuid,  # Murko returns coords as y, x
                    ),
                    "original_shape": (shape_y, shape_x),  # (y, x) to match Murko
                }
                uuid += 1
                omega += omega_step
            batch.append(results)
        messages.append({"type": "message", "data": batch})
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


def test_get_yz_least_squares():
    v_dists = [1, -2, -1, 2, 1, -2]
    omegas = [0, 90, 180, 270, 360, 450]
    result = get_yz_least_squares(v_dists, omegas)
    assert result[0] == approx(1)
    assert result[1] == approx(2)


def test_get_yz_least_squares_with_more_angles():
    v_dists = [1, -0.707, -2, -2.121, -1, 0.707, 2, 2.121, 1]
    omegas = [0, 45, 90, 135, 180, 225, 270, 315, 360]
    result = get_yz_least_squares(v_dists, omegas)
    assert result[0] == approx(1, abs=0.01)
    assert result[1] == approx(2, abs=0.01)


def test_process_result_appends_lists_with_correct_values(
    murko_results: MurkoResultsDevice,
):
    result = {
        "most_likely_click": (0.5, 0.3),  # (y, x)
        "original_shape": (100, 100),
    }
    metadata = MurkoMetadata(
        zoom_percentage=100.0,
        omega_angle=60.0,
        microns_per_x_pixel=5.0,
        microns_per_y_pixel=5.0,
        beam_centre_i=50,
        beam_centre_j=50,
        uuid="uuid",
        sample_id="test",
    )

    assert murko_results.x_dists_mm == []
    assert murko_results.y_dists_mm == []
    assert murko_results.omegas == []
    murko_results.process_result(result, metadata)
    assert murko_results.x_dists_mm == [0.2 * 100 * 5 / 1000]
    assert murko_results.y_dists_mm == [0]
    assert murko_results.omegas == [60]


@patch("dodal.devices.i04.murko_results.calculate_beam_distance")
def test_process_result_skips_when_no_result_from_murko(
    mock_calculate_beam_distance: MagicMock,
    murko_results: MurkoResultsDevice,
    caplog: pytest.LogCaptureFixture,
):
    result = {
        "most_likely_click": (-1, -1),  #  Murko could not find a most_likely_click
        "original_shape": (100, 100),
    }
    metadata = MurkoMetadata(
        zoom_percentage=100.0,
        omega_angle=60.0,
        microns_per_x_pixel=5.0,
        microns_per_y_pixel=5.0,
        beam_centre_i=50,
        beam_centre_j=50,
        uuid="uuid",
        sample_id="test",
    )

    with caplog.at_level("INFO"):
        murko_results.process_result(result, metadata)

    assert murko_results.x_dists_mm == []
    assert murko_results.y_dists_mm == []
    assert murko_results.omegas == []
    assert mock_calculate_beam_distance.call_count == 0
    assert "Murko didn't produce a result, moving on" in caplog.text


@patch("dodal.devices.i04.murko_results.MurkoResultsDevice.process_result")
@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_process_batch_makes_correct_calls(
    mock_strict_redis: MagicMock,
    mock_process_result: MagicMock,
    murko_results: MurkoResultsDevice,
):
    uuid = 0
    omega = 0
    batch = []

    for _ in range(2):
        results = {}
        for _ in range(3):
            results[uuid] = {
                "most_likely_click": (0.5, 0.5),
                "original_shape": (100, 100),  # (y, x) to match Murko
            }
            uuid += 1
            omega += 20
        batch.append(results)
    message = {"data": pickle.dumps(batch), "type": "message"}
    metadata = json_metadata(
        n=6,
        start=0,
        step=20,
        microns_pxp=10,
        microns_pyp=10,
        beam_centre_i=50,
        beam_centre_j=50,
    )
    _, murko_results.redis_client.hget = mock_redis_calls(
        mock_strict_redis, None, metadata
    )
    mock_hget = cast(MagicMock, murko_results.redis_client.hget)

    await murko_results.process_batch(message, sample_id="0")
    assert mock_hget.call_count == 6
    assert mock_process_result.call_count == 6
    assert mock_process_result.call_args_list[-1] == call(
        {"most_likely_click": (0.5, 0.5), "original_shape": (100, 100)},
        {
            "omega_angle": 100,
            "microns_per_x_pixel": 10,
            "microns_per_y_pixel": 10,
            "beam_centre_i": 50,
            "beam_centre_j": 50,
        },
    )


@patch("dodal.devices.i04.murko_results.MurkoResultsDevice.process_result")
async def test_process_batch_doesnt_process_result_if_no_metadata_for_certain_uuid(
    mock_process_result: MagicMock,
    murko_results: MurkoResultsDevice,
    caplog: pytest.LogCaptureFixture,
):
    batch = [
        {
            0: {
                "most_likely_click": (0.5, 0.5),
                "original_shape": (100, 100),
            },
            1: {
                "most_likely_click": (0.7, 0.7),
                "original_shape": (100, 100),
            },
        }
    ]
    message = {"data": pickle.dumps(batch), "type": "message"}

    murko_results.redis_client.hget = patch.object(
        murko_results.redis_client,
        "hget",
        new_callable=AsyncMock,
        side_effect=lambda *_: None,
    ).start()

    with caplog.at_level("INFO"):
        await murko_results.process_batch(message, sample_id="0")

    assert mock_process_result.call_count == 0
    assert "Found no metadata for uuid 0" in caplog.text
    assert "Found no metadata for uuid 1" in caplog.text


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_no_movement_given_sample_centre_matches_beam_centre(
    mock_strict_redis: MagicMock,
    murko_results: MurkoResultsDevice,
    mock_setters: tuple[MagicMock, MagicMock, MagicMock],
):
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        images_per_message=10, omega_start=50, omega_step=5
    )  # Crystal aligned with beam centre
    murko_results.pubsub.get_message, murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == 0, "wrong x"
    assert mock_y_setter.call_args[0][0] == 0, "wrong y"
    assert mock_z_setter.call_args[0][0] == 0, "wrong z"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_90_180_degrees(
    mock_strict_redis: MagicMock,
    murko_results: MurkoResultsDevice,
    mock_setters: tuple[MagicMock, MagicMock, MagicMock],
):
    x = 0.5
    y = 0.6
    z = 0.3
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        xyz=(x, y, z), beam_centre_i=90, beam_centre_j=40, shape_x=100, shape_y=100
    )
    murko_results.pubsub.get_message, murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await murko_results.trigger()

    assert mock_x_setter.call_args[0][0] == x - 0.9, "wrong x"
    assert mock_y_setter.call_args[0][0] == approx(y - 0.4), "wrong y"
    assert mock_z_setter.call_args[0][0] == approx(z), "wrong z"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_45_and_135_angles(
    mock_strict_redis: MagicMock,
    murko_results: MurkoResultsDevice,
    mock_setters: tuple[MagicMock, MagicMock, MagicMock],
):
    x = 0.5
    y = 0.3
    z = 0.4
    xyz = x, y, z
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        xyz=xyz, omega_start=45, omega_step=90, beam_centre_i=75, beam_centre_j=70
    )
    murko_results.pubsub.get_message, murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await murko_results.trigger()

    assert mock_x_setter.call_args[0][0] == x - 0.75, "wrong x"
    assert mock_y_setter.call_args[0][0] == approx(y - 0.7), "wrong y"
    assert mock_z_setter.call_args[0][0] == approx(z), "wrong z"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_correct_movement_given_multiple_angles_and_x_drift(
    mock_strict_redis: MagicMock,
    murko_results: MurkoResultsDevice,
    mock_setters: tuple[MagicMock, MagicMock, MagicMock],
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
    murko_results.pubsub.get_message, murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == approx(x + 0.055 - 0.75), "wrong x"
    assert mock_y_setter.call_args[0][0] == approx(y - 0.7), "wrong y"
    assert mock_z_setter.call_args[0][0] == approx(z), "wrong z"


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_trigger_calls_get_message_and_hget(
    mock_strict_redis: MagicMock,
    murko_results: MurkoResultsDevice,
):
    messages, metadata = get_messages(
        batches=4, messages_per_batch=3, images_per_message=2, omega_step=5
    )

    murko_results.pubsub.get_message, murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    await murko_results.trigger()

    mock_get_message = cast(MagicMock, murko_results.pubsub.get_message)
    mock_hget = cast(MagicMock, murko_results.redis_client.hget)

    # 4 messages to find, plus one None message
    assert mock_get_message.call_count == 5
    # 4 * 3 * 2 metadata messages
    assert mock_hget.call_count == 24


@patch("dodal.devices.i04.murko_results.StrictRedis")
async def test_trigger_stops_once_last_angle_found(
    mock_strict_redis: MagicMock,
    murko_results: MurkoResultsDevice,
):
    messages, metadata = get_messages(
        batches=5,
        messages_per_batch=3,
        images_per_message=2,
        omega_start=90,
        omega_step=10,
    )

    murko_results.pubsub.get_message, murko_results.redis_client.hget = (
        mock_redis_calls(mock_strict_redis, messages, metadata)
    )
    murko_results.stop_angle = 200
    await murko_results.trigger()

    mock_get_message = cast(MagicMock, murko_results.pubsub.get_message)
    mock_hget = cast(MagicMock, murko_results.redis_client.hget)

    # Takes 2 batches to find the last angle, 200°
    assert mock_get_message.call_count == 2
    # 2 batches of 6 = 12
    assert mock_hget.call_count == 12


async def test_assert_subscribes_to_queue_and_clears_results_on_stage(
    murko_results: MurkoResultsDevice,
):
    murko_results._x_mm_setter(1)
    murko_results._y_mm_setter(2)
    murko_results._z_mm_setter(3)

    murko_results.pubsub = (mock_pubsub := AsyncMock())
    await murko_results.stage()

    mock_pubsub.subscribe.assert_called_once_with("murko-results")
    assert await murko_results.x_mm.get_value() == 0
    assert await murko_results.y_mm.get_value() == 0
    assert await murko_results.z_mm.get_value() == 0


async def test_assert_unsubscribes_to_queue_on_unstage(
    murko_results: MurkoResultsDevice,
):
    murko_results.pubsub = (mock_pubsub := AsyncMock())
    await murko_results.unstage()

    mock_pubsub.unsubscribe.assert_called_once()
