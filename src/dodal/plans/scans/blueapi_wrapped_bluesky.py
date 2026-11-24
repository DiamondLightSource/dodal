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


def strip_parameter(func: Callable[P, R], parameter: str) -> Callable[P, R]:
    """Remove a default argument from a function's signature.

    Used for removing arguments from plans that are not serialisable
    so they can be used with blueapi.
    """
    func_signature = signature(func)

    if parameter not in func_signature.parameters:
        raise ValueError(
            f"Parameter {parameter!r} not found in {func.__name__!r} signature"
        )

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)

    wrapper.__signature__ = signature(func).replace(  # type: ignore
        parameters=[
            p for name, p in signature(func).parameters.items() if name != parameter
        ]
    )
    if wrapper.__doc__:
        wrapper.__doc__ = re.sub(
            rf"^(\s*){re.escape(parameter)}\s+:.*?(?=^\1\w+\s+:|\Z)",
            "",
            wrapper.__doc__,
            flags=re.DOTALL | re.MULTILINE,
        )

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
