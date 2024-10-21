import uuid
import warnings
from textwrap import dedent
from typing import Any

from dodal.common.types import Group


def group_uuid(name: str) -> Group:
    """
    Returns a unique but human-readable string, to assist debugging orchestrated groups.

    Args:
        name (str): A human readable name

    Returns:
        readable_uid (Group): name appended with a unique string
    """
    return f"{name}-{str(uuid.uuid4())[:6]}"


def inject(name: str) -> Any:  # type: ignore
    """
    Function to mark a defaulted argument of a plan as a reference to a device stored
    in another context and not available to be referenced directly.
    Bypasses type checking, returning x as Any and therefore valid as a default
    argument, leaving handling to the context from which the plan is called.
    Assumes that device.name is unique.
    e.g. For a 1-dimensional scan, that is usually performed on a Movable with
    name "stage_x"

    def scan(x: Movable = inject("stage_x"), start: float = 0.0 ...)

    Args:
        name (str): Name of a Device to be fetched from an external context

    Returns:
        Any: name but without typing checking, valid as any default type

    """

    warnings.warn(
        dedent("""
        Inject is deprecated, users are now expected to call the device factory
        functions in dodal directly, these will cache devices as singletons after
        they have been called once. For example:

        from bluesky.protocols import Readable
        from bluesky.utils import MsgGenerator
        from dodal.beamlines import i22

        def my_plan(detector: Readable = i22.saxs(connect_immediately=False)) -> MsgGenerator:
            ...

        Where previously the default would have been inject("saxs")
        """),
        DeprecationWarning,
        stacklevel=2,
    )
    return name
