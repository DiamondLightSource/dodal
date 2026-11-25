import inspect
from collections.abc import Callable
from typing import get_type_hints

import bluesky.plans as bp
import pytest

from dodal.plans.scans import (
    count,
    list_grid_scan,
    list_scan,
    rel_grid_scan,
    rel_list_grid_scan,
    rel_list_scan,
    rel_log_scan,
    scan,
)
from dodal.plans.scans.blueapi_wrapped_bluesky import (
    _strip_parameter_from_docstring,
    strip_parameter,
)


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
        # (rel_scan, "per_step"),
        # (log_scan, "per_step"),
        (rel_log_scan, "per_step"),
        (list_scan, "per_step"),
        (rel_list_scan, "per_step"),
        # (grid_scan, "per_step"),
        (rel_grid_scan, "per_step"),
        (list_grid_scan, "per_step"),
        (rel_list_grid_scan, "per_step"),
    ],
)
def test_bluesky_plan_has_non_serialisable_parameter_removed(plan, parameter):
    assert parameter not in inspect.signature(plan).parameters


def test_strip_parameter_removes_parameter_from_annotations_without_modifying_original():
    def plan(a: int, *, per_step: Callable | None = None, md: dict | None = None):
        yield a

    wrapped = strip_parameter(plan, "per_step")

    assert "per_step" not in wrapped.__annotations__
    assert "per_step" not in get_type_hints(wrapped)
    assert "per_step" in plan.__annotations__


def test_strip_parameter_raises_if_parameter_is_positional():
    def plan(a: int, per_step=None):
        yield a

    with pytest.raises(ValueError, match="must be keyword-only"):
        strip_parameter(plan, "per_step")


def test_strip_parameter_raises_if_parameter_has_no_default():
    def plan(a: int, *, per_step):
        yield a

    with pytest.raises(ValueError, match="must have a default"):
        strip_parameter(plan, "per_step")


@pytest.mark.parametrize(
    "doc, expected",
    [
        pytest.param(
            """Plan.

            Parameters
            ----------
            a : int
                First argument.
            per_step: callable
                Hook for each step.
            md : dict
                Metadata.
            """,
            """Plan.

            Parameters
            ----------
            a : int
                First argument.
            md : dict
                Metadata.
            """,
            id="no space before colon",
        ),
        pytest.param(
            """Plan.

            Parameters
            ----------
            a : int
                First argument.

                More about the first argument.

            per_step : callable
                Hook for each step.
            md : dict
                Metadata.
            """,
            """Plan.

            Parameters
            ----------
            a : int
                First argument.

                More about the first argument.

            md : dict
                Metadata.
            """,
            id="preceded by blank line",
        ),
        pytest.param(
            """Plan.

            Parameters
            ----------
            a : int
                First argument.
            per_step : callable
                Hook for each step. Expected signature ::

                    def f(detectors): ...

            See Also
            --------
            other_plan
            """,
            """Plan.

            Parameters
            ----------
            a : int
                First argument.

            See Also
            --------
            other_plan
            """,
            id="last parameter with blank line in description",
        ),
    ],
)
def test_strip_parameter_from_docstring_only_removes_parameter(doc: str, expected: str):
    assert _strip_parameter_from_docstring(doc, "per_step") == expected


@pytest.mark.parametrize(
    "plan, original, parameter",
    [
        (count, bp.count, "per_shot"),
        (scan, bp.scan, "per_step"),
        # (rel_scan, bp.rel_scan, "per_step"),
        # (log_scan, bp.log_scan, "per_step"),
        (rel_log_scan, bp.rel_log_scan, "per_step"),
        (list_scan, bp.list_scan, "per_step"),
        (rel_list_scan, bp.rel_list_scan, "per_step"),
        # (grid_scan, bp.grid_scan, "per_step"),
        (rel_grid_scan, bp.rel_grid_scan, "per_step"),
        (list_grid_scan, bp.list_grid_scan, "per_step"),
        (rel_list_grid_scan, bp.rel_list_grid_scan, "per_step"),
    ],
)
def test_bluesky_plan_docstring_only_has_non_serialisable_parameter_removed(
    plan, original, parameter
):
    assert parameter in original.__doc__
    assert parameter not in plan.__doc__
    # Everything else in the docstring (other parameters, See Also etc.) is kept.
    original_lines = [line.strip() for line in original.__doc__.splitlines()]
    kept_lines = [line.strip() for line in plan.__doc__.splitlines()]
    remaining = iter(original_lines)
    assert all(line in remaining for line in kept_lines)  # ordered subsequence
    for section in ("md", "See Also"):
        if section in original.__doc__:
            assert section in plan.__doc__
