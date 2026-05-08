import re
from collections.abc import Mapping, Sequence
from typing import cast

import pytest
from bluesky.protocols import Readable
from bluesky.run_engine import RunEngine
from event_model.documents import (
    Event,
    EventDescriptor,
    RunStart,
    RunStop,
    StreamResource,
)
from ophyd_async.core import (
    AsyncReadable,
    StandardDetector,
)
from ophyd_async.testing import assert_emitted
from pydantic import ValidationError

from dodal.devices.motors import Motor
from dodal.plans.wrapped import (
    _make_step_scan_args_and_shape,
    _make_stepped_list_num,
    _make_stepped_list_step,
    _round_list_elements,
    count,
    list_grid_rscan,
    list_grid_scan,
    list_rscan,
    list_scan,
    num_grid_rscan,
    num_grid_scan,
    num_rscan,
    num_scan,
    require,
    step_grid_rscan,
    step_grid_scan,
    step_rscan,
    step_scan,
)


def assert_expected_shape(
    run_engine_documents: Mapping[str, list[dict]], expected_shape: tuple[int, ...]
) -> None:
    start = run_engine_documents["start"][0]
    assert start["shape"] == expected_shape


def test_count_delay_validation(det: StandardDetector, run_engine: RunEngine):
    args: dict[float | Sequence[float], str] = {  # type: ignore
        # List wrong length
        (1,): "Number of delays given must be 2: was given 1",
        (1, 2, 3): "Number of delays given must be 2: was given 3",
        # Delay non-physical
        # negative time
        -1: "Input should be greater than or equal to 0",
        (-1, 2): "Input should be greater than or equal to 0",
        # # null time
        None: "Input should be a valid number",
        (None, 2): "Input should be a valid number",
        # # NaN time
        "foo": "Input should be a valid number",
        ("foo", 2): "Input should be a valid number",
    }
    for delay, reason in args.items():
        with pytest.raises((ValidationError, AssertionError), match=reason):
            run_engine(count([det], num=3, delay=delay))


def test_count_detectors_validation(run_engine: RunEngine):
    args: dict[str, Sequence[Readable | AsyncReadable]] = {
        # No device to read
        "1 validation error for count": set(),
        # Not Readable
        "Input should be an instance of Sequence": set("foo"),  # type: ignore
    }
    for reason, dets in args.items():
        with pytest.raises(ValidationError, match=reason):
            run_engine(count(dets))


def test_count_num_validation(det: StandardDetector, run_engine: RunEngine):
    args: dict[int, str] = {
        -1: "Input should be greater than or equal to 1",
        0: "Input should be greater than or equal to 1",
        "str": "Input should be a valid integer",  # type: ignore
    }
    for num, reason in args.items():
        with pytest.raises(ValidationError, match=reason):
            run_engine(count([det], num=num))


@pytest.mark.parametrize("num, shape", ([1, (1,)], [3, (3,)]))
def test_count_plan_produces_expected_start_document(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
    num: int,
    shape: tuple[int, ...],
):
    run_engine(count([det], num=num))
    start = run_engine_documents.get("start")
    assert start and len(start) == 1
    run_start = cast(RunStart, start[0])
    assert (hints := run_start.get("hints")) and (
        hints.get("dimensions") == [(("time",), "primary")]
    )
    assert_expected_shape(run_engine_documents, (num,))


@pytest.mark.parametrize("num, length", ([1, 1], [3, 3]))
def test_count_plan_produces_expected_stop_document(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
    num: int,
    length: tuple[int, ...],
):
    run_engine(count([det], num=num))
    stop = run_engine_documents.get("stop")
    assert stop and len(stop) == 1
    run_stop = cast(RunStop, stop[0])
    assert run_stop.get("num_events") == {"primary": length}
    assert run_stop.get("exit_status") == "success"


def test_count_plan_produces_expected_descriptor(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
):
    run_engine(count([det], num=1))
    desc = run_engine_documents.get("descriptor")
    assert desc and len(desc) == 1
    event_desc = cast(EventDescriptor, desc[0])
    object_keys = event_desc.get("object_keys")
    assert object_keys is not None and det.name in object_keys
    assert event_desc.get("name") == "primary"


@pytest.mark.parametrize("num, length", ([1, 1], [3, 3]))
def test_count_plan_produces_expected_events(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
    num: int,
    length: tuple[int, ...],
):
    run_engine(count([det], num=num))
    event_docs = run_engine_documents.get("event")
    assert event_docs and len(event_docs) == length
    for i in range(len(event_docs)):
        event = cast(Event, event_docs[i])
        assert not event.get("data")  # empty data
        assert event.get("seq_num") == i + 1


@pytest.mark.parametrize("num", [1, 3])
def test_count_plan_produces_expected_resources(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
    num: int,
):
    run_engine(count([det], num=num))
    stream_resource_docs = run_engine_documents.get("stream_resource")
    data_keys = [det.name, f"{det.name}-sum"]
    assert stream_resource_docs and len(stream_resource_docs) == len(data_keys)
    for i in range(len(stream_resource_docs)):
        resource = cast(StreamResource, stream_resource_docs[i])
        assert resource.get("data_key") == data_keys[i]


@pytest.mark.parametrize("num, length", ([1, 1], [3, 3]))
def test_count_plan_produces_expected_datums(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    det: StandardDetector,
    num: int,
    length: tuple[int, ...],
):
    run_engine(count([det], num=num))
    stream_datum = run_engine_documents.get("stream_datum")
    data_keys = [det.name, f"{det.name}-sum"]
    assert stream_datum and len(stream_datum) == len(data_keys) * length


def test_count_with_no_detector_raise_error(run_engine: RunEngine):
    with pytest.raises(ValidationError):
        run_engine(count([]))


def _assert_emitted(
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    num: int,
    start: int = 1,
    descriptor: int = 1,
    stream_resource: int = 2,
    stop: int = 1,
) -> None:
    numbers = {
        "start": start,
        "descriptor": descriptor,
        "event": num,
        "stop": stop,
    }
    # If detector, add stream parts.
    if len(detectors) > 0:
        # Order matters
        numbers = {
            "start": start,
            "descriptor": descriptor,
            "stream_resource": stream_resource,
            "stream_datum": num * stream_resource,
            "event": num,
            "stop": stop,
        }
    assert_emitted(run_engine_documents, **numbers)


@pytest.fixture(params=[0, 1], ids=["0 detector(s)", "1 detector(s)"])
def detectors(
    request: pytest.FixtureRequest, det: StandardDetector
) -> Sequence[StandardDetector]:
    return [] if request.param == 0 else [det]


@pytest.mark.parametrize("x_list, num", ([[0.0, 2.2], 5], [[1.1, -1.1], 3]))
def test_num_scan_with_one_axis(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    num: int,
):
    run_engine(num_scan(detectors=detectors, params=[x_axis, *x_list], num=num))
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


@pytest.mark.parametrize(
    "x_list, y_list, num", ([[-1.1, 1.1], [2.2, -2.2], 5], [[0, 1.1], [2.2, 3.3], 5])
)
def test_num_scan_with_two_axes(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
    num: int,
):
    run_engine(
        num_scan(
            detectors=detectors,
            params=[x_axis, *x_list, y_axis, *y_list],
            num=num,
        )
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


def test_num_scan_fails_when_given_wrong_number_of_params(
    run_engine: RunEngine, detectors: Sequence[StandardDetector], x_axis: Motor
):
    with pytest.raises(ValueError):
        run_engine(num_scan(detectors=detectors, params=[x_axis, -1, 1, 5], num=5))


@pytest.mark.parametrize(
    "x_list, y_list, num",
    ([[-1, 1], [2, 0], 0], [[-1, 1], [-1, 1], 3.5], [[-1, 1], [-1, 1], -2]),
)
def test_num_scan_fails_when_given_bad_info(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
    num: int,
):
    with pytest.raises(ValueError):
        run_engine(
            num_scan(
                detectors=detectors,
                params=[x_axis, *x_list, y_axis, *y_list],
                num=num,
            )
        )


@pytest.mark.parametrize(
    "x_list, y_list", ([(-1.1, 1.1, 5), (2.2, -2.2, 3)], [(0, 1.1, 5), (2.2, 3.3, 5)])
)
def test_num_grid_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: tuple[float, float, int],
    y_axis: Motor,
    y_list: tuple[float, float, int],
):
    num = int(x_list[-1] * y_list[-1])
    run_engine(
        num_grid_scan(
            detectors=detectors,
            params=[x_axis, *x_list, y_axis, *y_list],
        )
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (x_list[2], y_list[2]))


@pytest.mark.parametrize(
    "x_list, y_list", ([(-1.1, 1.1, 5), (2.2, -2.2, 3)], [(0, 1.1, 5), (2.2, 3.3, 5)])
)
def test_num_grid_scan_when_not_snaking(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: tuple[float, float, int],
    y_axis: Motor,
    y_list: tuple[float, float, int],
):
    num = int(x_list[-1] * y_list[-1])
    run_engine(
        num_grid_scan(
            detectors=detectors,
            params=[x_axis, *x_list, y_axis, *y_list],
            snake_axes=False,
        )
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (x_list[2], y_list[2]))


def test_num_grid_scan_fails_when_given_wrong_number_of_params(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(ValueError):
        run_engine(
            num_grid_scan(detectors=detectors, params=[x_axis, 0, 1.1, 2, y_axis, 1.1])
        )


@pytest.mark.parametrize(
    "x_list, y_list", ([[-1.1, 1.1, 5], [2.2, -2.2, 3]], [[0, 1.1, 5], [2.2, 3.3, 5]])
)
def test_num_scan_fails_when_asked_to_snake_slow_axis(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
):
    with pytest.raises(ValueError):
        run_engine(
            num_grid_scan(
                detectors=detectors,
                params=[x_axis, *x_list, y_axis, *y_list],
                snake_axes=[x_axis],
            )
        )


@pytest.mark.parametrize("x_list, num", ([[0.0, 2.2], 5], [[1.1, -1.1], 3]))
def test_num_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    num: int,
):
    run_engine(num_rscan(detectors=detectors, params=[x_axis, *x_list], num=num))
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


@pytest.mark.parametrize(
    "x_list, y_list, num", ([[-1.1, 1.1], [2.2, -2.2], 5], [[0, 1.1], [2.2, 3.3], 5])
)
def test_num_rscan_with_two_axes(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
    num: int,
):
    run_engine(
        num_rscan(
            detectors=detectors, params=[x_axis, *x_list, y_axis, *y_list], num=num
        )
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


@pytest.mark.parametrize(
    "x_list, y_list, num", ([[-1, 1], [2, 0], 0], [[-1, 1], [-1, 1], 3.5])
)
def test_num_rscan_fails_when_given_bad_info(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
    num: int,
):
    with pytest.raises(ValueError):
        run_engine(
            num_rscan(
                detectors=detectors,
                params=[x_axis, *x_list, y_axis, *y_list],
                num=num,
            )
        )


@pytest.mark.parametrize(
    "x_list, y_list", ([(-1.1, 1.1, 5), (2.2, -2.2, 3)], [(0, 1.1, 5), (2.2, 3.3, 5)])
)
def test_num_grid_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: tuple[float, float, int],
    y_axis: Motor,
    y_list: tuple[float, float, int],
):
    num = int(x_list[-1] * y_list[-1])
    run_engine(
        num_grid_rscan(
            detectors=detectors,
            params=[x_axis, *x_list, y_axis, *y_list],
        )
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (x_list[2], y_list[2]))


@pytest.mark.parametrize(
    "x_list, y_list", ([(-1.1, 1.1, 5), (2.2, -2.2, 3)], [(0, 1.1, 5), (2.2, 3.3, 5)])
)
def test_num_grid_rscan_when_not_snaking(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: tuple[float, float, int],
    y_axis: Motor,
    y_list: tuple[float, float, int],
):
    num = int(x_list[-1] * y_list[-1])
    run_engine(
        num_grid_rscan(
            detectors=detectors,
            params=[x_axis, *x_list, y_axis, *y_list],
            snake_axes=False,
        )
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (x_list[2], y_list[2]))


@pytest.mark.parametrize(
    "x_list, y_list", ([[-1.1, 1.1, 5], [2.2, -2.2, 3]], [[0, 1.1, 5], [2.2, 3.3, 5]])
)
def test_num_grid_rscan_fails_when_asked_to_snake_slow_axis(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
):
    with pytest.raises(ValueError):
        run_engine(
            num_grid_rscan(
                detectors=detectors,
                params=[x_axis, *x_list, y_axis, *y_list],
                snake_axes=[x_axis],
            )
        )


@pytest.mark.parametrize(
    "x_list, y_list, grid, final_shape, final_length",
    (
        [[0, 10, 1], [0, 5], False, (11,), 4],
        [[0, 10, 1], [0, 5, 1], True, (11, 6), 4],
    ),
)
def test_make_step_scan_args_and_shape(
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
    grid: bool,
    final_shape: list,
    final_length: int,
):
    args, shape = _make_step_scan_args_and_shape(
        params=[x_axis, *x_list, y_axis, *y_list], grid=grid
    )
    assert len(args) == final_length
    assert shape == final_shape


def test_make_list_scan_args_fails_when_lists_are_different_lengths(
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(ValueError):
        _make_step_scan_args_and_shape(
            params=[x_axis, 0, 1, 2, y_axis, 0, 1, 2, 3], grid=False
        )


@pytest.mark.parametrize("x_list", ([0, 1, 2, 3], [1.1, 2.2, 3.3]))
def test_list_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
):
    num = len(x_list)
    run_engine(list_scan(detectors=detectors, params=[x_axis, x_list]))
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


@pytest.mark.parametrize(
    "x_list, y_list",
    (
        [[3, 2, 1], [1, 2, 3]],
        [[-1.1, -2.2, -3.3, -4.4, -5.5], [1.1, 2.2, 3.3, 4.4, 5.5]],
    ),
)
def test_list_scan_with_two_axes(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
):
    num = int(len(x_list))
    run_engine(list_scan(detectors=detectors, params=[x_axis, x_list, y_axis, y_list]))
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


def test_list_scan_fails_with_differnt_list_lengths(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(ValueError):
        run_engine(
            list_scan(
                detectors=detectors,
                params=[x_axis, [1, 2, 3, 4, 5], y_axis, [1, 2, 3, 4]],
            )
        )


@pytest.mark.parametrize(
    "x_list, y_list",
    (
        [[3, 2, 1], [1, 2, 3, 4]],
        [[-1.1, -2.2, -3.3, -4.4, -5.5], [1.1, 2.2, 3.3, 4.4, 5.5]],
    ),
)
def test_list_grid_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
):
    num = int(len(x_list) * len(y_list))
    run_engine(
        list_grid_scan(detectors=detectors, params=[x_axis, x_list, y_axis, y_list])
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (len(x_list), len(y_list)))


@pytest.mark.parametrize("x_list", ([0, 1, 2, 3], [1.1, 2.2, 3.3]))
def test_list_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
):
    num = int(len(x_list))
    run_engine(list_rscan(detectors=detectors, params=[x_axis, x_list]))
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (len(x_list),))


@pytest.mark.parametrize(
    "x_list, y_list",
    (
        [[3, 2, 1], [1, 2, 3]],
        [[-1.1, -2.2, -3.3, -4.4, -5.5], [1.1, 2.2, 3.3, 4.4, 5.5]],
    ),
)
def test_list_rscan_with_two_axes(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
):
    num = int(len(x_list))

    run_engine(list_rscan(detectors=detectors, params=[x_axis, x_list, y_axis, y_list]))
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


def test_list_rscan_fails_with_differnt_list_lengths(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(ValueError):
        run_engine(
            list_rscan(
                detectors=detectors,
                params=[x_axis, [1, 2, 3, 4, 5], y_axis, [1, 2, 3, 4]],
            )
        )


@pytest.mark.parametrize(
    "x_list, y_list",
    (
        [[3, 2, 1], [1, 2, 3, 4]],
        [[-1.1, -2.2, -3.3, -4.4, -5.5], [1.1, 2.2, 3.3, 4.4, 5.5]],
    ),
)
def test_list_grid_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list,
    y_axis: Motor,
    y_list: list,
):
    num = int(len(x_list) * len(y_list))

    run_engine(
        list_grid_rscan(detectors=detectors, params=[x_axis, x_list, y_axis, y_list])
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (len(x_list), len(y_list)))


@pytest.mark.parametrize(
    "stepped_list, params, rounded_element",
    (
        [[0.1234, 1.1234, 2.1234], [0.123, 2.123, 1], 0.123],
        [[0.1234, 1.1234, 2.1234], [0.12, 2.12, 1], 0.12],
        [[0.1234, 1.1234, 2.1234], [0.1, 2.1, 1], 0.1],
        [[0.1234, 1.1234, 2.1234], [0, 2, 1], 0],
    ),
)
def test_round_list_elements(
    stepped_list: list[float], params: list[float], rounded_element: float
):
    rounded_list = _round_list_elements(stepped_list, params)
    assert rounded_list[0] == rounded_element


@pytest.mark.parametrize(
    "start, stop, step",
    (
        [-1, 1, 0.1],
        [-2, 2, 0.2],
        [1, -1, -0.1],
        [2, -2, -0.2],
        [1, -1, 0.1],
        [2, -2, 0.2],
    ),
)
def test_make_stepped_list_step(start: float, stop: float, step: float):
    stepped_list = _make_stepped_list_step(start, stop, step)
    stepped_list_length = len(stepped_list)
    assert stepped_list_length == 21
    assert stepped_list[0] / stepped_list[-1] == -1
    assert stepped_list[10] == 0


def test_make_stepped_list_step_with_large_step():
    stepped_list = _make_stepped_list_step(0, 1, 5)
    stepped_list_length = len(stepped_list)
    assert stepped_list_length == 2
    assert stepped_list[0] == 0
    assert stepped_list[-1] == 1


@pytest.mark.parametrize("start, step", ([-1, 0.1], [-2, 0.2], [1, -0.1], [2, -0.2]))
def test_make_stepped_list_num(start: float, step: float):
    stepped_list = _make_stepped_list_num(start, step, num=21)
    stepped_list_length = len(stepped_list)
    assert stepped_list_length == 21
    assert stepped_list[0] / stepped_list[-1] == -1
    assert stepped_list[10] == 0


def test_make_stepped_list_num_fails_when_num_is_zero():
    start = stop = 1.1
    with pytest.raises(
        ValueError,
        match=re.escape(
            f"Start ({start}) and stop ({stop}) values cannot be the same."
        ),
    ):
        _make_stepped_list_step(start=start, stop=stop, step=0.25)


def test_make_stepped_list_num_fails_when_given_equal_start_and_stop_values():
    with pytest.raises(ValueError, match="Number of points must be greater than zero."):
        _make_stepped_list_num(start=1, step=0.1, num=0)


def test_require_raises_error_if_not_correct_type():
    with pytest.raises(
        ValueError, match="Parameter test must be one of type str, got int."
    ):
        require(value=5, expected=str, name="test")


@pytest.mark.parametrize(
    "x_list, y_list, z_list, grid",
    (
        [[0, 1], [0, 0.2], [0, 0.5], False],
        [[0, 1, 0.25], [0, 0.2], [0, 1, 0.2, 0.5], False],
        [[0, 1, 0.25], [0, 0.2], [0, 1, 0.5], True],
        [[0, 1, 0.25], [0, 1, 0.2], [0, 0.5], True],
    ),
)
def test_make_step_scan_args_fails_when_given_incorrect_number_of_parameters(
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
    z_axis: Motor,
    z_list: list[float | int],
    grid: bool,
):
    with pytest.raises(ValueError):
        _make_step_scan_args_and_shape(
            params=[x_axis, *x_list, y_axis, *y_list, z_axis, *z_list], grid=grid
        )


@pytest.mark.parametrize(
    "x_list, num", ([[0, 1, 0.1], 11], [[-1, 1, 0.1], 21], [[0, 10, 1], 11])
)
def test_step_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    num,
):
    run_engine(step_scan(detectors=detectors, params=[x_axis, *x_list]))
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


@pytest.mark.parametrize(
    "x_list, y_list, num",
    (
        [[0, 1, 0.25], [0, 0.1], 5],
        [[-1, 1, 0.25], [-1, 0.1], 9],
        [[0, 10, 2.5], [0, 1], 5],
    ),
)
def test_step_scan_with_multiple_axes(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
    num,
):
    run_engine(
        step_scan(detectors=detectors, params=[x_axis, *x_list, y_axis, *y_list])
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


@pytest.mark.parametrize(
    "x_list, expected_num_x, y_list, expected_num_y, snake",
    (
        [[0, 1, 0.25], 5, [0, 2, 0.5], 5, True],
        [[0, 1, 0.25], 5, [0, 2, 0.5], 5, False],
        [[-1, 1, 0.25], 9, [1, -1, -0.5], 5, True],
        [[-1, 1, 0.25], 9, [1, -1, -0.5], 5, False],
        [[0, 10, 2.5], 5, [0, -10, -2.5], 5, True],
        [[0, 10, 2.5], 5, [0, -10, -2.5], 5, False],
    ),
)
def test_step_grid_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    expected_num_x: int,
    y_axis: Motor,
    y_list: list[float | int],
    expected_num_y: int,
    snake: bool,
):
    run_engine(
        step_grid_scan(
            detectors=detectors,
            params=[x_axis, *x_list, y_axis, *y_list],
            snake_axes=snake,
        )
    )
    _assert_emitted(run_engine_documents, detectors, expected_num_x * expected_num_y)
    assert_expected_shape(run_engine_documents, (expected_num_x, expected_num_y))


@pytest.mark.parametrize(
    "x_list, y_list", ([[0, 1, 0.1], [0, 1, 0.1, 1]], [[0, 1, 0.1], [0]])
)
def test_step_grid_scan_fails_when_given_incorrect_number_of_params(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
):
    with pytest.raises(ValueError):
        run_engine(
            step_grid_scan(
                detectors=detectors, params=[x_axis, *x_list, y_axis, *y_list]
            )
        )


@pytest.mark.parametrize(
    "x_list, num",
    ([[0, 1, 0.1], 11], [[-1, 1, 0.1], 21], [[0, 10, 1], 11]),
)
def test_step_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    num: int,
):
    run_engine(step_rscan(detectors=detectors, params=[x_axis, *x_list]))
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


@pytest.mark.parametrize(
    "x_list, y_list, num",
    (
        [[0, 1, 0.25], [0, 0.1], 5],
        [[-1, 1, 0.25], [-1, 0.1], 9],
        [[0, 10, 2.5], [0, 1], 5],
    ),
)
def test_step_rscan_with_multiple_axes(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
    num: int,
):
    run_engine(
        step_rscan(detectors=detectors, params=[x_axis, *x_list, y_axis, *y_list])
    )
    _assert_emitted(run_engine_documents, detectors, num)
    assert_expected_shape(run_engine_documents, (num,))


@pytest.mark.parametrize(
    "x_list, expected_num_x, y_list, expected_num_y, snake",
    (
        [[0, 1, 0.25], 5, [0, 2, 0.5], 5, True],
        [[0, 1, 0.25], 5, [0, 2, 0.5], 5, False],
        [[-1, 1, 0.25], 9, [1, -1, -0.5], 5, True],
        [[-1, 1, 0.25], 9, [1, -1, -0.5], 5, False],
        [[0, 10, 2.5], 5, [0, -10, -2.5], 5, True],
        [[0, 10, 2.5], 5, [0, -10, -2.5], 5, False],
    ),
)
def test_step_grid_rscan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    expected_num_x: int,
    y_axis: Motor,
    y_list: list[float | int],
    expected_num_y: int,
    snake: bool,
):
    run_engine(
        step_grid_rscan(
            detectors=detectors,
            params=[x_axis, *x_list, y_axis, *y_list],
            snake_axes=snake,
        )
    )
    _assert_emitted(run_engine_documents, detectors, expected_num_x * expected_num_y)
    assert_expected_shape(run_engine_documents, (expected_num_x, expected_num_y))


@pytest.mark.parametrize("x_list, y_list", ([[0, 1], [0, 1, 0.1]], [[0], [0, 1, 0.1]]))
def test_step_grid_scan_fails_when_given_wrong_number_of_args_for_first_axes(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
):
    with pytest.raises(
        ValueError,
        match="The axis must be movable, start, stop, step.",
    ):
        run_engine(
            step_grid_scan(
                detectors=detectors, params=[x_axis, *x_list, y_axis, *y_list]
            )
        )


@pytest.mark.parametrize(
    "x_list, y_list", ([[0, 1, 0.1], [0, 1, 0.1, 1]], [[0, 1, 0.1], [0]])
)
def test_step_grid_scan_fails_when_given_wrong_number_of_args_for_second_axes(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
):
    with pytest.raises(
        ValueError,
        match="The axis must be movable, start, stop, step.",
    ):
        run_engine(
            step_grid_scan(
                detectors=detectors, params=[x_axis, *x_list, y_axis, *y_list]
            )
        )


@pytest.mark.parametrize(
    "x_list, y_list", ([[0, 1, 0.1], [0, 1, 0.1]], [[0, 1, 0.1], [0]])
)
def test_step_scan_fails_when_given_wrong_number_of_args_for_second_axes(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
    x_list: list[float | int],
    y_axis: Motor,
    y_list: list[float | int],
):
    with pytest.raises(
        ValueError,
        match="The axis must be movable, start, stop.",
    ):
        run_engine(
            step_scan(detectors=detectors, params=[x_axis, *x_list, y_axis, *y_list])
        )


def test_make_step_scan_args_and_shape_fails_with_invalid_type_args(
    x_axis: Motor,
    y_axis: Motor,
):
    with pytest.raises(
        ValueError,
        match="Scan syntax only takes movables or numbers for params.",
    ):
        _make_step_scan_args_and_shape(
            [x_axis, 1, "3", 1, y_axis, 1, "4", 1],  # type: ignore
            grid=True,
        )
        _make_step_scan_args_and_shape(
            [x_axis, 1, "3", 1, y_axis, 1, "4"],  # type: ignore
            grid=False,
        )


def test_step_scan_fails_with_step_size_zero(
    run_engine: RunEngine,
    detectors: Sequence[StandardDetector],
    x_axis: Motor,
):
    with pytest.raises(
        ValueError,
        match="Step size must be greater than zero.",
    ):
        run_engine(step_scan(detectors=detectors, params=[x_axis, 1, 5, 0]))
