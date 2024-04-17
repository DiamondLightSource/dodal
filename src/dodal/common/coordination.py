import uuid

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


def inject(name: str):  # type: ignore
    """
    Function to mark a default argument of a plan method as a reference to a device
    that is stored in the Blueapi context, as devices are constructed on startup of the
    service, and are not available to be used when writing plans.
    Bypasses mypy linting, returning x as Any and therefore valid as a default
    argument.
    e.g. For a 1-dimensional scan, that is usually performed on a consistent Movable
    axis with name "stage_x"
    def scan(x: Movable = inject("stage_x"), start: float = 0.0 ...)

    Args:
        name (str): Name of a device to be fetched from the Blueapi context

    Returns:
        Any: name but without typing checking, valid as any default type

    """

    return name
