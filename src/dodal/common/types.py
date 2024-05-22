from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Generator,
)

from bluesky import RunEngine
from bluesky.utils import Msg
from ophyd_async.core import DirectoryProvider

# String identifier used by 'wait' or stubs that await
Group = str
# A true 'plan', usually the output of a generator function
MsgGenerator = Generator[Msg, Any, None]
# A function that generates a plan
PlanGenerator = Callable[..., MsgGenerator]


class RunEngineAwareDirectoryProvider(DirectoryProvider, ABC):
    @abstractmethod
    def connect_to_run_engine(self, run_engine: RunEngine) -> None: ...


class UpdatingDirectoryProvider(DirectoryProvider, ABC):
    @abstractmethod
    async def update(self, **kwargs) -> None: ...
