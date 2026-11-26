import inspect
from collections.abc import Callable
from typing import get_type_hints

import bluesky.plans as bp
import pytest

from dodal.plans.scans import blueapi_wrapped_bluesky as bw


def _plan(
    a: int, b: float, *, per_step: Callable | None = None, md: dict | None = None
):
    """A test plan.

    Parameters
    ----------
    a : int
        First argument.
    per_step : callable
        Hook for each step.
    md : dict
        Metadata.
    """
    yield a, b, per_step


def test_strip_parameter_removes_parameter_from_signature_hints_and_docstring():
    wrapped = bw.strip_parameter(_plan, "per_step")

    assert list(inspect.signature(wrapped).parameters) == ["a", "b", "md"]
    assert "per_step" not in get_type_hints(wrapped)
    assert wrapped.__doc__ == _plan.__doc__.replace(  # type: ignore
        "    per_step : callable\n        Hook for each step.\n", ""
    )


def test_strip_parameter_does_not_modify_original_function():
    signature, doc, annotations = (
        inspect.signature(_plan),
        _plan.__doc__,
        dict(_plan.__annotations__),
    )

    bw.strip_parameter(_plan, "per_step")

    assert inspect.signature(_plan) == signature
    assert _plan.__doc__ == doc
    assert _plan.__annotations__ == annotations


def test_strip_parameter_preserves_function_identity_and_behaviour():
    wrapped = bw.strip_parameter(_plan, "per_step")

    assert wrapped.__name__ == _plan.__name__
    assert wrapped.__qualname__ == _plan.__qualname__
    assert wrapped.__module__ == _plan.__module__
    assert list(wrapped(1, 2.0)) == [(1, 2.0, None)]


def _positional(a: int, per_step=None):
    yield a


def _no_default(a: int, *, per_step):
    yield a


@pytest.mark.parametrize(
    "func, parameter, match",
    [
        (_plan, "per_shot", "Parameter 'per_shot' not found in '_plan' signature"),
        (_positional, "per_step", "must be keyword-only"),
        (_no_default, "per_step", "must have a default"),
    ],
)
def test_strip_parameter_raises_for_invalid_parameter(
    func: Callable, parameter: str, match: str
):
    with pytest.raises(ValueError, match=match):
        bw.strip_parameter(func, parameter)


@pytest.mark.parametrize(
    "doc, expected",
    [
        pytest.param(
            """
            a : int
                First argument.
            per_step: callable
                Hook for each step.
            md : dict
            """,
            """
            a : int
                First argument.
            md : dict
            """,
            id="no space before colon",
        ),
        pytest.param(
            """
            a : int
                First argument.

            per_step : callable
                Hook for each step.
            md : dict
            """,
            """
            a : int
                First argument.

            md : dict
            """,
            id="preceded by blank line",
        ),
        pytest.param(
            """
            a : int
            per_step : callable
                Hook for each step. Expected signature ::

                    def f(detectors): ...

            See Also
            --------
            """,
            """
            a : int

            See Also
            --------
            """,
            id="last parameter with blank line in description",
        ),
    ],
)
def test_strip_parameter_from_docstring_only_removes_parameter(doc: str, expected: str):
    assert bw._strip_parameter_from_docstring(doc, "per_step") == expected


@pytest.mark.parametrize(
    "plan",
    [
        bw.count,
        bw.scan,
        # bw.rel_scan,
        # bw.log_scan,
        bw.rel_log_scan,
        bw.list_scan,
        bw.rel_list_scan,
        # grid_scan
        bw.rel_grid_scan,
        bw.list_grid_scan,
        bw.rel_list_grid_scan,
    ],
    ids=lambda plan: plan.__name__,
)
def test_wrapped_bluesky_plan_only_has_non_serialisable_parameter_removed(plan):
    original = getattr(bp, plan.__name__)
    assert plan.__wrapped__ is original

    removed = set(inspect.signature(original).parameters) - set(
        inspect.signature(plan).parameters
    )
    assert removed in ({"per_step"}, {"per_shot"})
    (parameter,) = removed

    assert parameter not in plan.__doc__
    # Every remaining docstring line is from the original, in the same order.
    original_lines = iter(original.__doc__.splitlines())
    assert all(line in original_lines for line in plan.__doc__.splitlines())
    assert "md" in plan.__doc__
