from abc import ABC, abstractmethod
from collections.abc import Callable

from bluesky.utils import MsgGenerator
from ophyd_async.core import PathProvider

# String identifier used by 'wait' or stubs that await
Group = str
# A function that generates a plan
PlanGenerator = Callable[..., MsgGenerator]


class UpdatingPathProvider(PathProvider, ABC):
    @abstractmethod
    async def data_session(self) -> str: ...
    @abstractmethod
    async def update(self, **kwargs) -> None: ...
