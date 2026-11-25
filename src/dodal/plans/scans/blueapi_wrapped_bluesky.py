import re
from collections.abc import Callable
from functools import wraps
from inspect import signature
from typing import ParamSpec, TypeVar

import bluesky.plans as bp

"""This module wraps plan(s) from bluesky.plans for blueapi. These plans expose
per_step/per_shot arguments which are callable. A callable is a python method and are
not serialisable, therefore it is impossible for the user to override this argument. It
will be confusing to leave this in for a user, so the parameter and doc string
referencing it is removed https://github.com/DiamondLightSource/blueapi/issues/711.
"""


P = ParamSpec("P")
R = TypeVar("R")


def _strip_parameter_from_docstring(doc: str, parameter: str) -> str:
    """Remove a parameter's entry from a numpydoc style "Parameters" section.

    Removes the line `<parameter> : <type>` (with or without a space before the colon)
    along with its description, i.e. every following line that is indented further
    than the parameter name. Blank lines are only removed if they are followed by more
    of the description, so the next parameter or section is never touched.
    """
    pattern = (
        rf"^([ \t]*){re.escape(parameter)}[ \t]*:.*"  # "per_step : callable" line
        r"(?:\n(?:[ \t]*\n)*\1[ \t]+\S.*)*"  # more indented description lines
        r"\n?"
    )
    return re.sub(pattern, "", doc, flags=re.MULTILINE)


def strip_parameter(func: Callable[P, R], parameter: str) -> Callable[P, R]:
    """Remove a keyword-only argument from a function's signature and docstring.

    Used for removing arguments from plans that are not serialisable (such as the
    `per_step` callable) so the plans don't have this option with blueapi. The returned
    wrapper calls `func` unchanged, so the removed argument always takes its default value.

    Args:
        func: The function to wrap.
        parameter: Name of the keyword-only argument, with a default, to remove.

    Returns:
        A wrapper around `func` whose signature, annotations and docstring no longer
        include `parameter`.

    Raises:
        ValueError: If `parameter` is not in the signature of `func`, is not
            keyword-only or has no default value.
    """
    func_signature = signature(func)
    param = func_signature.parameters.get(parameter)
    if param is None:
        raise ValueError(
            f"Parameter {parameter!r} not found in {func.__name__!r} signature"
        )
    # Removing a positional parameter from the signature would make callers' positional
    # arguments bind to the wrong parameters, and removing a parameter without a
    # default would make the function impossible to call.
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


# Commented out ones won't work until bluesky version has
# https://github.com/bluesky/bluesky/pull/2125 fixed due to missing typing.
count = strip_parameter(bp.count, "per_shot")
scan = strip_parameter(bp.scan, "per_step")
# rel_scan = strip_parameter(bp.rel_scan, "per_step")
# log_scan = strip_parameter(bp.log_scan, "per_step")
rel_log_scan = strip_parameter(bp.rel_log_scan, "per_step")

list_scan = strip_parameter(bp.list_scan, "per_step")
rel_list_scan = strip_parameter(bp.rel_list_scan, "per_step")

# grid_scan = strip_parameter(bp.grid_scan, "per_step")
rel_grid_scan = strip_parameter(bp.rel_grid_scan, "per_step")
list_grid_scan = strip_parameter(bp.list_grid_scan, "per_step")
rel_list_grid_scan = strip_parameter(bp.rel_list_grid_scan, "per_step")
