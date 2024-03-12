from typing import (
    Any,
    Callable,
    Generator,
)

from bluesky.utils import Msg

# String identifier used by 'wait' or stubs that await
Group = str
# A true 'plan', usually the output of a generator function
MsgGenerator = Generator[Msg, Any, None]
# A function that generates a plan
PlanGenerator = Callable[..., MsgGenerator]
