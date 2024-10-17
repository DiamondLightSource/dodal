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
