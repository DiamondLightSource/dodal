import re

import pytest
from bluesky import RunEngine

from dodal.plans import get_run_engine_metadata


def test_good_get_run_engine_metadata(run_engine: RunEngine):
    test_string = "blah"
    test_int = 5
    test_float = 4.4

    run_engine.md["test_string"] = test_string
    run_engine.md["test_int"] = test_int
    run_engine.md["test_float"] = test_float

    def test_plan():
        assert (yield from get_run_engine_metadata("test_string")) == test_string
        assert (yield from get_run_engine_metadata("test_int", int)) == test_int
        assert (yield from get_run_engine_metadata("test_float", int)) == test_float

    run_engine(test_plan())


def test_get_run_engine_metadata_fails_on_bad_type(run_engine: RunEngine):
    not_a_float = "[Oh no, I can't be converted to a float!]"
    run_engine.md["not_a_float"] = not_a_float

    def test_plan():
        yield from get_run_engine_metadata("not_a_float", float)

    with pytest.raises(
        TypeError,
        match=re.escape(
            f"Requested RunEngine metadata '{not_a_float}' could not be converted to requested type '{float}'"
        ),
    ):
        run_engine(test_plan())


def test_get_run_engine_metadata_fails_on_missing_metadata(run_engine: RunEngine):
    missing_metadata = "missing_metadata"

    def test_plan():
        yield from get_run_engine_metadata(missing_metadata, float)

    with pytest.raises(
        ValueError,
        match=re.escape(
            f"Requested RunEngine metadata '{missing_metadata}' could not be found"
        ),
    ):
        run_engine(test_plan())
