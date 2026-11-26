"""bluesky.plans for blueapi, without their per_step/per_shot callable arguments.

Callables are not serialisable, so blueapi users can never set them. See
https://github.com/DiamondLightSource/blueapi/issues/711.
"""

import re
from collections.abc import Callable
from functools import wraps
from inspect import signature
from typing import ParamSpec, TypeVar

import bluesky.plans as bp

P = ParamSpec("P")
R = TypeVar("R")


def _strip_parameter_from_docstring(doc: str, parameter: str) -> str:
    """Remove `parameter` and its more-indented description from a numpydoc
    docstring, leaving the rest untouched.
    """
    pattern = (
        rf"^([ \t]*){re.escape(parameter)}[ \t]*:.*"  # "per_step : callable" line
        r"(?:\n(?:[ \t]*\n)*\1[ \t]+\S.*)*"  # more indented description lines
        r"\n?"
    )
    return re.sub(pattern, "", doc, flags=re.MULTILINE)


def strip_parameter(func: Callable[P, R], parameter: str) -> Callable[P, R]:
    """Wrap `func` without `parameter` in its signature, annotations or docstring.

    Used to hide non-serialisable plan arguments from blueapi. The removed argument
    always takes its default.

    Args:
        func: The function to wrap.
        parameter: A keyword-only argument with a default.

    Raises:
        ValueError: If `parameter` is missing, not keyword-only or has no default.
    """
    func_signature = signature(func)
    param = func_signature.parameters.get(parameter)
    if param is None:
        raise ValueError(
            f"Parameter {parameter!r} not found in {func.__name__!r} signature"
        )
    # Removing a positional arg would misbind callers' args, and one without a
    # default would make func uncallable.
    if param.kind is not param.KEYWORD_ONLY:
        raise ValueError(
            f"Parameter {parameter!r} of {func.__name__!r} must be keyword-only to be "
            "removed"
        )
    if param.default is param.empty:
        raise ValueError(
            f"Parameter {parameter!r} of {func.__name__!r} must have a default to be "
            "removed"
        )

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)

    wrapper.__signature__ = func_signature.replace(  # type: ignore
        parameters=[
            p for name, p in func_signature.parameters.items() if name != parameter
        ]
    )
    # wraps() assigns func's own __annotations__ dict, copy it so func is unchanged.
    wrapper.__annotations__ = {
        name: annotation
        for name, annotation in func.__annotations__.items()
        if name != parameter
    }
    if wrapper.__doc__:
        wrapper.__doc__ = _strip_parameter_from_docstring(wrapper.__doc__, parameter)

    return wrapper


count = strip_parameter(bp.count, "per_shot")
scan = strip_parameter(bp.scan, "per_step")
rel_scan = strip_parameter(bp.rel_scan, "per_step")
log_scan = strip_parameter(bp.log_scan, "per_step")
rel_log_scan = strip_parameter(bp.rel_log_scan, "per_step")

list_scan = strip_parameter(bp.list_scan, "per_step")
rel_list_scan = strip_parameter(bp.rel_list_scan, "per_step")

grid_scan = strip_parameter(bp.grid_scan, "per_step")
rel_grid_scan = strip_parameter(bp.rel_grid_scan, "per_step")
list_grid_scan = strip_parameter(bp.list_grid_scan, "per_step")
rel_list_grid_scan = strip_parameter(bp.rel_list_grid_scan, "per_step")
