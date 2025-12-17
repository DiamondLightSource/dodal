import json
import logging
import pickle
from typing import Any
from unittest.mock import AsyncMock, MagicMock, call, patch

import numpy as np
import pytest
from ophyd_async.core import init_devices
from pytest import approx

from dodal.devices.i04.murko_results import (
    RESULTS_COMPLETE_MESSAGE,
    MurkoMetadata,
    MurkoResult,
    MurkoResultsDevice,
    NoResultsFoundError,
    get_yz_least_squares,
)


@pytest.fixture
@patch("dodal.devices.i04.murko_results.StrictRedis")
async def murko_results(mock_strict_redis: MagicMock) -> MurkoResultsDevice:
    with init_devices(mock=True):
        murko_results = MurkoResultsDevice(name="murko_results")
    murko_results.pubsub = AsyncMock()
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


@pytest.fixture
async def default_metadata() -> MurkoMetadata:
    return MurkoMetadata(
        zoom_percentage=100.0,
        omega_angle=60.0,
        microns_per_x_pixel=5.0,
        microns_per_y_pixel=5.0,
        beam_centre_i=50,
        beam_centre_j=50,
        uuid="uuid",
        sample_id="test",
        used_for_centring=None,
    )


def mock_redis_calls(mock_strict_redis, messages: list, metadata: dict):
    iter_messages = iter(messages)
    mock_get_message = patch.object(
        mock_strict_redis.pubsub,
        "get_message",
        new_callable=AsyncMock,
        side_effect=lambda *args, **kwargs: next(iter_messages),
    ).start()
    mock_hget = patch.object(
        mock_strict_redis,
        "hget",
        new_callable=AsyncMock,
        side_effect=lambda _, uuid: metadata[uuid],
    ).start()
    mock_hset = AsyncMock()
    return mock_get_message, mock_hget, mock_hset


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


def get_messages(
    batches: int = 2,
    results_per_batch: int = 1,
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
) -> tuple[list, dict]:
    """Generate mock Murko messages and metadata with accurate most_likely_click values,
    based on x, y, z and a range of omega values. By default, xyz lines up with the beam
    centre."""
    messages = []
    uuid = 0
    omega = omega_start
    x, y, z = xyz
    for _ in range(batches):
        batch = []
        for _ in range(results_per_batch):
            results = (
                str(uuid),
                {
                    "most_likely_click": (
                        get_y_after_rotation(omega, y, z, beam_centre_j, shape_y),
                        x + x_drift * uuid,  # Murko returns coords as y, x
                    ),
                    "original_shape": (shape_y, shape_x),  # (y, x) to match Murko
                },
            )
            uuid += 1
            omega += omega_step
            batch.append(results)
        messages.append({"type": "message", "data": pickle.dumps(batch)})
    messages.append({"type": "message", "data": pickle.dumps(RESULTS_COMPLETE_MESSAGE)})

    metadata = json_metadata(
        n=batches * results_per_batch,
        start=omega_start,
        step=omega_step,
        microns_pxp=microns_pxp,
        microns_pyp=microns_pyp,
        beam_centre_i=beam_centre_i,
        beam_centre_j=beam_centre_j,
    )
    return messages, metadata


def json_metadata(
    n: int,
    start: float = 90,
    step: float = 1,
    microns_pxp: float = 10,
    microns_pyp: float = 10,
    beam_centre_i: int = 50,
    beam_centre_j: int = 50,
    uuid: str = "UUID",
) -> dict[str, Any]:
    metadatas: dict[str, Any] = {}
    for i in range(n):
        metadata = {
            "omega_angle": start + step * i,
            "microns_per_x_pixel": microns_pxp,
            "microns_per_y_pixel": microns_pyp,
            "beam_centre_i": beam_centre_i,
            "beam_centre_j": beam_centre_j,
            "uuid": uuid,
        }
        metadatas[str(i)] = json.dumps(metadata)
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
    murko_results: MurkoResultsDevice, default_metadata: MurkoMetadata
):
    result = {
        "most_likely_click": (0.5, 0.3),  # (y, x)
        "original_shape": (100, 100),
    }

    assert murko_results._results == []
    murko_results.process_result(result, default_metadata)
    assert len(murko_results._results) == 1
    assert murko_results._results[0].x_dist_mm == 0.2 * 100 * 5 / 1000
    assert murko_results._results[0].y_dist_mm == 0
    assert murko_results._results[0].omega == 60


@patch("dodal.devices.i04.murko_results.calculate_beam_distance")
def test_process_result_skips_when_no_result_from_murko(
    mock_calculate_beam_distance: MagicMock,
    murko_results: MurkoResultsDevice,
    caplog: pytest.LogCaptureFixture,
    default_metadata: MurkoMetadata,
):
    result = {
        "most_likely_click": (-1, -1),  #  Murko could not find a most_likely_click
        "original_shape": (100, 100),
    }

    with caplog.at_level("INFO"):
        murko_results.process_result(result, default_metadata)

    assert murko_results._results == []
    assert mock_calculate_beam_distance.call_count == 0
    assert "Murko didn't produce a result, moving on" in caplog.text


@patch("dodal.devices.i04.murko_results.MurkoResultsDevice.process_result")
async def test_process_batch_makes_correct_calls(
    mock_process_result: MagicMock,
    murko_results: MurkoResultsDevice,
):
    uuid = 0
    omega = 0
    batch = []

    for _ in range(6):
        result = (
            str(uuid),
            {
                "most_likely_click": (0.5, 0.5),
                "original_shape": (100, 100),  # (y, x) to match Murko
            },
        )
        uuid += 1
        omega += 20
        batch.append(result)
    metadata = json_metadata(
        n=6,
        start=0,
        step=20,
        microns_pxp=10,
        microns_pyp=10,
        beam_centre_i=50,
        beam_centre_j=50,
    )
    _, murko_results.redis_client.hget, _ = mock_redis_calls(
        murko_results.redis_client, [], metadata
    )
    mock_hget = murko_results.redis_client.hget

    await murko_results.process_batch(batch, sample_id="0")
    assert mock_hget.call_count == 6  # type: ignore
    assert mock_process_result.call_count == 6
    assert mock_process_result.call_args_list[-1] == call(
        {"most_likely_click": (0.5, 0.5), "original_shape": (100, 100)},
        {
            "omega_angle": 100,
            "microns_per_x_pixel": 10,
            "microns_per_y_pixel": 10,
            "beam_centre_i": 50,
            "beam_centre_j": 50,
            "uuid": "UUID",
        },
    )


@patch("dodal.devices.i04.murko_results.MurkoResultsDevice.process_result")
async def test_process_batch_doesnt_process_result_if_no_metadata_for_certain_uuid(
    mock_process_result: MagicMock,
    murko_results: MurkoResultsDevice,
    caplog: pytest.LogCaptureFixture,
):
    batch = [
        (
            "0",
            {
                "most_likely_click": (0.5, 0.5),
                "original_shape": (100, 100),
            },
        ),
        (
            "1",
            {
                "most_likely_click": (0.7, 0.7),
                "original_shape": (100, 100),
            },
        ),
    ]

    murko_results.redis_client.hget = patch.object(
        murko_results.redis_client,
        "hget",
        new_callable=AsyncMock,
        side_effect=lambda *_: None,
    ).start()

    with caplog.at_level("INFO"):
        await murko_results.process_batch(batch, sample_id="0")

    assert mock_process_result.call_count == 0
    assert "Found no metadata for uuid 0" in caplog.text
    assert "Found no metadata for uuid 1" in caplog.text


async def test_no_movement_given_sample_centre_matches_beam_centre(
    murko_results: MurkoResultsDevice,
    mock_setters: tuple[MagicMock, MagicMock, MagicMock],
):
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        results_per_batch=10, omega_start=50, omega_step=5
    )  # Crystal aligned with beam centre
    (
        murko_results.pubsub.get_message,
        murko_results.redis_client.hget,
        murko_results.redis_client.hset,
    ) = mock_redis_calls(murko_results.redis_client, messages, metadata)
    await murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == 0, "wrong x"
    assert mock_y_setter.call_args[0][0] == 0, "wrong y"
    assert mock_z_setter.call_args[0][0] == 0, "wrong z"


async def test_correct_movement_given_90_180_degrees(
    murko_results: MurkoResultsDevice,
    mock_setters: tuple[MagicMock, MagicMock, MagicMock],
):
    x = 0.5
    y = 0.6
    z = 0.3
    murko_results.PERCENTAGE_TO_USE = 100  # type:ignore
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        xyz=(x, y, z),
        omega_start=90,
        omega_step=90,
        beam_centre_i=90,
        beam_centre_j=40,
        shape_x=100,
        shape_y=100,
    )
    (
        murko_results.pubsub.get_message,
        murko_results.redis_client.hget,
        murko_results.redis_client.hset,
    ) = mock_redis_calls(murko_results.redis_client, messages, metadata)
    await murko_results.trigger()

    assert mock_x_setter.call_args[0][0] == x - 0.9, "wrong x"
    assert mock_y_setter.call_args[0][0] == approx(y - 0.4), "wrong y"
    assert mock_z_setter.call_args[0][0] == approx(z), "wrong z"


async def test_correct_movement_given_45_and_135_angles(
    murko_results: MurkoResultsDevice,
    mock_setters: tuple[MagicMock, MagicMock, MagicMock],
):
    murko_results.PERCENTAGE_TO_USE = 100  # type:ignore
    x = 0.5
    y = 0.3
    z = 0.4
    xyz = x, y, z
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        xyz=xyz, omega_start=45, omega_step=90, beam_centre_i=75, beam_centre_j=70
    )
    (
        murko_results.pubsub.get_message,
        murko_results.redis_client.hget,
        murko_results.redis_client.hset,
    ) = mock_redis_calls(murko_results.redis_client, messages, metadata)
    await murko_results.trigger()

    assert mock_x_setter.call_args[0][0] == x - 0.75, "wrong x"
    assert mock_y_setter.call_args[0][0] == approx(y - 0.7), "wrong y"
    assert mock_z_setter.call_args[0][0] == approx(z), "wrong z"


async def test_correct_movement_given_multiple_angles_and_x_drift(
    murko_results: MurkoResultsDevice,
    mock_setters: tuple[MagicMock, MagicMock, MagicMock],
):
    murko_results.PERCENTAGE_TO_USE = 100  # type:ignore
    x = 0.7
    y = 0.2
    z = 0.3
    xyz = (x, y, z)
    mock_x_setter, mock_y_setter, mock_z_setter = mock_setters
    messages, metadata = get_messages(
        batches=2,
        results_per_batch=6,
        xyz=xyz,
        omega_start=22.4,
        omega_step=20.7,
        beam_centre_i=75,
        beam_centre_j=70,
        x_drift=0.01,
    )
    (
        murko_results.pubsub.get_message,
        murko_results.redis_client.hget,
        murko_results.redis_client.hset,
    ) = mock_redis_calls(murko_results.redis_client, messages, metadata)
    await murko_results.trigger()
    assert mock_x_setter.call_args[0][0] == approx(x + 0.055 - 0.75), "wrong x"
    assert mock_y_setter.call_args[0][0] == approx(y - 0.7), "wrong y"
    assert mock_z_setter.call_args[0][0] == approx(z), "wrong z"


async def test_trigger_calls_get_message_and_hget(
    murko_results: MurkoResultsDevice,
):
    messages, metadata = get_messages(batches=4, results_per_batch=6, omega_step=5)

    (
        murko_results.pubsub.get_message,
        murko_results.redis_client.hget,
        murko_results.redis_client.hset,
    ) = mock_redis_calls(murko_results.redis_client, messages, metadata)
    await murko_results.trigger()

    mock_get_message = murko_results.pubsub.get_message
    mock_hget = murko_results.redis_client.hget

    # 4 results + 1 RESULTS_COMPLETE_MESSAGE to find
    assert mock_get_message.call_count == 5  # type: ignore
    # 4 * 3 * 2 metadata messages
    assert mock_hget.call_count == 24  # type: ignore


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


@pytest.mark.parametrize(
    "total_from_murko, percentage_to_keep, expected_left",
    [(100, 25, 25), (10, 25, 2), (1000, 1, 10), (8, 100, 8), (5, 50, 2)],
)
def test_given_n_results_filter_outliers_will_reduce_down_to_smaller_amount(
    total_from_murko: int,
    percentage_to_keep: int,
    expected_left: int,
    murko_results: MurkoResultsDevice,
):
    murko_results._results = [
        MurkoResult(
            chosen_point_px=(i + 11, 100),
            x_dist_mm=i,
            y_dist_mm=i,
            omega=i,
            uuid=str(i),
            metadata={},  # type:ignore
        )
        for i in range(total_from_murko)
    ]

    murko_results.PERCENTAGE_TO_USE = percentage_to_keep  # type:ignore

    filtered_results = murko_results.filter_outliers()

    assert isinstance(filtered_results, list)
    assert len(filtered_results) == expected_left


def test_when_results_filtered_then_smallest_x_pixels_kept(
    murko_results: MurkoResultsDevice,
):
    murko_results._results = [
        MurkoResult(
            chosen_point_px=(100, 0),
            x_dist_mm=4,
            y_dist_mm=8,
            omega=0,
            uuid="a",
            metadata={},  # type:ignore
        ),
        MurkoResult(
            chosen_point_px=(300, 100),
            x_dist_mm=0,
            y_dist_mm=90,
            omega=10,
            uuid="b",
            metadata={},  # type:ignore
        ),
        MurkoResult(
            chosen_point_px=(50, 200),
            x_dist_mm=6,
            y_dist_mm=63,
            omega=20,
            uuid="c",
            metadata={},  # type:ignore
        ),
        MurkoResult(
            chosen_point_px=(300, 300),
            x_dist_mm=7,
            y_dist_mm=8,
            omega=30,
            uuid="d",
            metadata={},  # type:ignore
        ),
    ]

    filtered_results = murko_results.filter_outliers()
    assert len(filtered_results) == 1
    results = filtered_results[0]
    assert results.chosen_point_px == (50, 200)
    assert results.x_dist_mm == 6
    assert results.y_dist_mm == 63
    assert results.omega == 20
    assert results.uuid == "c"


async def test_when_no_results_from_redis_then_expected_error_message_on_trigger(
    murko_results: MurkoResultsDevice,
):
    murko_results.pubsub.get_message.return_value = {  # type: ignore
        "type": "message",
        "data": pickle.dumps(RESULTS_COMPLETE_MESSAGE),
    }
    with pytest.raises(NoResultsFoundError):
        await murko_results.trigger()
        assert murko_results._results == []


async def test_when_results_device_unstaged_then_results_cleared_and_last_omega_reset(
    murko_results: MurkoResultsDevice,
):
    murko_results._results = [
        MurkoResult(
            chosen_point_px=(100, 100),
            x_dist_mm=4,
            y_dist_mm=8,
            omega=0,
            uuid="a",
            metadata={},  # type:ignore
        )
    ]
    murko_results._last_omega = 360

    await murko_results.unstage()

    assert not murko_results._results
    assert murko_results._last_omega is None


async def test_none_result_does_not_stop_results_device(
    murko_results: MurkoResultsDevice,
):
    messages, metadata = get_messages(
        batches=2,
        results_per_batch=1,
        omega_start=90,
        omega_step=90,
    )
    messages = list(messages)
    messages = [None] + [messages[0]] + [None] + messages[1:]

    assert messages[0] is None
    assert messages[2] is None

    (
        murko_results.pubsub.get_message,
        murko_results.redis_client.hget,
        murko_results.redis_client.hset,
    ) = mock_redis_calls(murko_results.redis_client, messages, metadata)
    mock_get_message = murko_results.pubsub.get_message
    mock_hget = murko_results.redis_client.hget

    await murko_results.trigger()

    assert mock_get_message.call_count == 5  # type: ignore
    assert mock_hget.call_count == 2  # 2 non None results  # type: ignore


def test_when_results_filtered_then_used_for_centring_field_is_correct(
    murko_results: MurkoResultsDevice, default_metadata: MurkoMetadata
):
    murko_results._results = [
        MurkoResult(
            chosen_point_px=(100, 0),
            x_dist_mm=4,
            y_dist_mm=8,
            omega=0,
            uuid="a",
            metadata=default_metadata.copy(),
        ),
        MurkoResult(
            chosen_point_px=(300, 100),
            x_dist_mm=0,
            y_dist_mm=90,
            omega=10,
            uuid="b",
            metadata=default_metadata.copy(),
        ),
        MurkoResult(
            chosen_point_px=(50, 200),
            x_dist_mm=6,
            y_dist_mm=63,
            omega=20,
            uuid="c",
            metadata=default_metadata.copy(),
        ),
        MurkoResult(
            chosen_point_px=(300, 300),
            x_dist_mm=7,
            y_dist_mm=8,
            omega=30,
            uuid="d",
            metadata=default_metadata.copy(),
        ),
    ]
    filtered_results = murko_results.filter_outliers()
    assert len(filtered_results) == 1
    used_result = filtered_results[0]
    assert used_result.chosen_point_px == (50, 200)
    assert used_result.x_dist_mm == 6
    assert used_result.y_dist_mm == 63
    assert used_result.omega == 20
    assert used_result.uuid == "c"
    assert used_result.metadata["used_for_centring"] is True
    assert len(murko_results._results) == 4
    for result in murko_results._results:
        if result == used_result:
            assert result.metadata["used_for_centring"] is True
        else:
            assert result.metadata["used_for_centring"] is False


async def test_correct_hset_calls_are_made_for_used_and_unused_results(
    murko_results: MurkoResultsDevice,
):
    messages, metadata = get_messages(
        batches=4,
        results_per_batch=6,
        omega_step=5,
        omega_start=90,
    )

    (
        murko_results.pubsub.get_message,
        murko_results.redis_client.hget,
        murko_results.redis_client.hset,
    ) = mock_redis_calls(murko_results.redis_client, messages, metadata)
    murko_results.PERCENTAGE_TO_USE = 50  # type:ignore
    await murko_results.trigger()

    mock_hset = murko_results.redis_client.hset

    expected_calls = []
    for result in murko_results._results:
        expected_calls.append(
            call.mock_hset("murko::metadata", result.uuid, json.dumps(result.metadata))
        )

    assert mock_hset.call_count == 24
    mock_hset.assert_has_calls(expected_calls, any_order=True)


def test_results_with_tiny_x_pixel_value_are_filtered_out(
    murko_results: MurkoResultsDevice, default_metadata: MurkoMetadata
):
    murko_results.PERCENTAGE_TO_USE = 100  # type: ignore
    murko_results._results = [
        MurkoResult(
            chosen_point_px=(500, 0),
            x_dist_mm=4,
            y_dist_mm=8,
            omega=0,
            uuid="a",
            metadata=default_metadata.copy(),
        ),
        MurkoResult(
            chosen_point_px=(0, 100),
            x_dist_mm=0,
            y_dist_mm=90,
            omega=10,
            uuid="b",
            metadata=default_metadata.copy(),
        ),
        MurkoResult(
            chosen_point_px=(5, 200),
            x_dist_mm=6,
            y_dist_mm=63,
            omega=20,
            uuid="c",
            metadata=default_metadata.copy(),
        ),
        MurkoResult(
            chosen_point_px=(9, 300),
            x_dist_mm=7,
            y_dist_mm=8,
            omega=30,
            uuid="d",
            metadata=default_metadata.copy(),
        ),
    ]
    filtered_results = murko_results.filter_outliers()
    assert len(filtered_results) == 1
    used_result = filtered_results[0]
    assert used_result.chosen_point_px == (500, 0)
    assert used_result == murko_results._results[0]
    assert len(murko_results._results) == 4
    for result in murko_results._results:
        if result == used_result:
            assert result.metadata["used_for_centring"] is True
        else:
            assert result.metadata["used_for_centring"] is False


async def test_trigger_stops_once_results_complete_message_received(
    murko_results: MurkoResultsDevice,
    caplog: pytest.LogCaptureFixture,
):
    messages, metadata = get_messages(
        batches=5,
        results_per_batch=10,
    )

    messages = (
        [messages[0]]
        + [{"type": "message", "data": pickle.dumps(RESULTS_COMPLETE_MESSAGE)}]
        + messages[1:]
    )

    assert pickle.loads(messages[1]["data"]) == RESULTS_COMPLETE_MESSAGE
    assert len(messages) == 7

    (
        murko_results.pubsub.get_message,
        murko_results.redis_client.hget,
        murko_results.redis_client.hset,
    ) = mock_redis_calls(murko_results.redis_client, messages, metadata)

    with caplog.at_level(logging.INFO):
        await murko_results.trigger()

    # Second message is RESULTS_COMPLETE_MESSAGE
    assert murko_results.pubsub.get_message.call_count == 2
    # One batch of 10 results is retrieved
    assert murko_results.redis_client.hget.call_count == 10

    assert any(
        record.message
        == f"Received results complete message: {RESULTS_COMPLETE_MESSAGE}"
        and record.levelname == "INFO"
        for record in caplog.records
    )


@patch("dodal.devices.i04.murko_results.time.time")
async def test_trigger_stops_if_no_message_in_5_seconds_and_raises_warning(
    mock_time: MagicMock,
    murko_results: MurkoResultsDevice,
    caplog: pytest.LogCaptureFixture,
):
    mock_time.side_effect = [1, 7, 8]
    messages, metadata = get_messages(batches=2)

    (
        murko_results.pubsub.get_message,
        murko_results.redis_client.hget,
        murko_results.redis_client.hset,
    ) = mock_redis_calls(murko_results.redis_client, messages, metadata)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(NoResultsFoundError):
            await murko_results.trigger()

    assert murko_results.pubsub.get_message.call_count == 0

    assert any(
        record.message
        == f"Time since last result > 5, expected to receive {RESULTS_COMPLETE_MESSAGE}"
        and record.levelname == "WARNING"
        for record in caplog.records
    )
