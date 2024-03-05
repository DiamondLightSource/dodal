from typing import (
    Annotated,
    Any,
    Callable,
    Generator,
)

from bluesky.utils import Msg

Group = Annotated[str, "String identifier used by 'wait' or stubs that await"]
MsgGenerator = Annotated[
    Generator[Msg, Any, None],
    "A true 'plan', usually the output of a generator function",
]
PlanGenerator = Annotated[
    Callable[..., MsgGenerator], "A function that generates a plan"
]
