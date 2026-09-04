import pytest

from dodal.plans.scans.annotations import (
    MovableListOfPoints,
    MovableStartStep,
    MovableStartStop,
    MovableStartStopNum,
    MovableStartStopStep,
)


@pytest.fixture
def trajectories_start_stop(
    request: pytest.FixtureRequest,
) -> list[MovableStartStop]:
    return [
        (request.getfixturevalue(axis), start, stop)
        for axis, start, stop in request.param
    ]


@pytest.fixture
def trajectories_start_stop_num(
    request: pytest.FixtureRequest,
) -> list[MovableStartStopNum]:
    return [
        (request.getfixturevalue(axis), start, stop, num)
        for axis, start, stop, num in request.param
    ]


@pytest.fixture
def trajectories_with_list(
    request: pytest.FixtureRequest,
) -> list[MovableListOfPoints]:
    return [(request.getfixturevalue(axis), points) for axis, points in request.param]


@pytest.fixture
def trajectories_start_step(
    request: pytest.FixtureRequest,
) -> list[MovableStartStep]:
    return [
        (request.getfixturevalue(axis), start, step)
        for axis, start, step in request.param
    ]


@pytest.fixture
def trajectories_start_stop_step(
    request: pytest.FixtureRequest,
) -> list[MovableStartStopStep]:
    return [
        (request.getfixturevalue(axis), start, stop, step)
        for axis, start, stop, step in request.param
    ]
