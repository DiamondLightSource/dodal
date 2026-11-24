import inspect

import pytest

from dodal.plans.scans import (
    count,
    grid_scan,
    list_grid_scan,
    list_scan,
    log_scan,
    rel_grid_scan,
    rel_list_grid_scan,
    rel_list_scan,
    rel_log_scan,
    rel_scan,
    scan,
)
from dodal.plans.scans.blueapi_wrapped_bluesky import strip_parameter


def test_strip_parameter_removes_parameter_from_signature():
    def plan(a: int, b: float, *, per_step=None, md=None):
        yield a, b

    wrapped = strip_parameter(plan, "per_step")

    assert "per_step" not in inspect.signature(wrapped).parameters
    assert list(inspect.signature(wrapped).parameters) == ["a", "b", "md"]


def test_strip_parameter_raises_if_parameter_does_not_exist():
    def plan(a: int, b: float):
        yield a, b

    with pytest.raises(
        ValueError, match="Parameter 'per_step' not found in 'plan' signature"
    ):
        strip_parameter(plan, "per_step")


def test_strip_parameter_preserves_original_function_metadata():
    def plan(a: int, b: float, *, per_step=None):
        """A test plan."""
        yield a, b

    wrapped = strip_parameter(plan, "per_step")

    assert wrapped.__name__ == plan.__name__
    assert wrapped.__qualname__ == plan.__qualname__
    assert wrapped.__module__ == plan.__module__
    assert wrapped.__annotations__ == plan.__annotations__
    assert wrapped.__doc__ == plan.__doc__


def test_strip_parameter_removes_parameter_from_docstring():
    def plan(a: int, b: float, *, per_step=None, md=None):
        """A test plan.

        Parameters
        ----------
        a : int
            First argument.
        b : float
            Second argument.
        per_step : callable
            Hook for each step.
        md : dict
            Metadata.
        """
        yield a, b

    wrapped = strip_parameter(plan, "per_step")
    assert wrapped.__doc__ is not None

    assert "per_step" not in wrapped.__doc__
    assert "Hook for each step." not in wrapped.__doc__
    assert "a : int" in wrapped.__doc__
    assert "b : float" in wrapped.__doc__
    assert "md : dict" in wrapped.__doc__


def test_strip_parameter_preserves_original_function_behaviour():
    calls = []

    def plan(a: int, b: float, *, per_step=None):
        calls.append((a, b, per_step))
        yield a, b

    wrapped = strip_parameter(plan, "per_step")

    result = list(wrapped(1, 2.0))

    assert result == [(1, 2.0)]
    assert calls == [(1, 2.0, None)]


def test_strip_parameter_does_not_modify_original_function():
    def plan(a: int, b: float, *, per_step=None):
        """A test plan.

        Parameters
        ----------
        per_step : callable
            Hook for each step.
        """
        yield a, b

    original_signature = inspect.signature(plan)
    original_doc = plan.__doc__

    wrapped = strip_parameter(plan, "per_step")

    assert "per_step" in inspect.signature(plan).parameters
    assert inspect.signature(plan) == original_signature
    assert plan.__doc__ == original_doc

    assert "per_step" not in inspect.signature(wrapped).parameters
    assert wrapped.__doc__ is not None
    assert "per_step" not in wrapped.__doc__


@pytest.mark.parametrize(
    "plan, parameter",
    [
        (count, "per_shot"),
        (scan, "per_step"),
        (rel_scan, "per_step"),
        (log_scan, "per_step"),
        (rel_log_scan, "per_step"),
        (list_scan, "per_step"),
        (rel_list_scan, "per_step"),
        (grid_scan, "per_step"),
        (rel_grid_scan, "per_step"),
        (list_grid_scan, "per_step"),
        (rel_list_grid_scan, "per_step"),
    ],
)
def test_bluesky_plan_has_non_serialisable_parameter_removed(plan, parameter):
    assert parameter not in inspect.signature(plan).parameters
