from .coordination import group_uuid
from .maths import in_micros, step_to_num
from .types import PlanGenerator

__all__ = [
    "group_uuid",
    "in_micros",
    "PlanGenerator",
    "step_to_num",
]


def __getattr__(name):
    if name == "MsgGenerator":
        raise DeprecationWarning("import from bluesky.utils instead")
    if name == "inject":
        raise DeprecationWarning("Use result of dodal device call instead")

    return globals()[name]
