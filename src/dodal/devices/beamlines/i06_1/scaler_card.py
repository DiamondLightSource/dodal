from typing import Generic, TypeVar

from ophyd_async.core import (
    AsyncStatus,
    DeviceVector,
    Reference,
    StandardReadable,
    StandardReadableFormat,
)
from ophyd_async.epics.core import epics_signal_rw, epics_signal_x

T = TypeVar("T", bound=DeviceVector)


class ScalerCardController(StandardReadable):
    def __init__(
        self, prefix: str, start_count_suffix: str, count_suffix: str, name: str = ""
    ):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.integration_time = epics_signal_rw(float, prefix + count_suffix)

        # Should this be enum True/False, Done/Count, signal x ?
        self.start_count = epics_signal_x(prefix + start_count_suffix)
        super().__init__(name)


class ScalerCardChannels(StandardReadable, Generic[T]):
    def __init__(self, channels: T, controller: ScalerCardController, name: str = ""):
        with self.add_children_as_readables():
            self.channels = channels

        for value in channels.values():
            controller.add_readables([value])

        self.controller_ref = Reference(controller)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        self.controller_ref().integration_time.set(value)

    @AsyncStatus.wrap
    async def trigger(self):
        await self.controller_ref().start_count.trigger()
        # await set_and_wait_for_value(self.counting, True, wait_for_set_completion=True)
        # await wait_for_good_state(self.counting, {False})
