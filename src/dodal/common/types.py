from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from typing import (
    Any,
)

from bluesky.utils import Msg
from ophyd_async.core import DirectoryProvider

# String identifier used by 'wait' or stubs that await
Group = str
# A true 'plan', usually the output of a generator function
MsgGenerator = Generator[Msg, Any, None]
# A function that generates a plan
PlanGenerator = Callable[..., MsgGenerator]


class UpdatingDirectoryProvider(DirectoryProvider, ABC):
    @abstractmethod
    def update(self, **kwargs) -> None: ...
