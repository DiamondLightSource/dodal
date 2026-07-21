import asyncio
from typing import Generic, TypeVar

from bluesky.protocols import Movable, Reading, Triggerable
from ophyd_async.core import (
    AsyncStatus,
    Device,
    DeviceMock,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    default_mock_class,
    set_mock_value,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_rw


class MockScalerCardController(DeviceMock["ScalerCardController"]):
    async def _complete(self):
        await asyncio.sleep(0.01)
        set_mock_value(self._counting, False)

    def _on_value(self, value: dict[str, Reading[bool]]):
        if value[self._counting.name]["value"]:
            asyncio.create_task(self._complete())

    async def connect(self, device):
        self._counting = device.start_count

        set_mock_value(device.start_count, False)
        # Can't use callback_on_mock_put as this is called before the mock put, we need
        # to simulate after mock put update. subscribe_reading listeners are stored in
        # a set, so repeatedly subscribing this bound method is harmless and does not
        # create duplicate callbacks.
        device.start_count.subscribe_reading(self._on_value)


@default_mock_class(MockScalerCardController)
class ScalerCardController(StandardReadable, Triggerable, Movable[float]):
    """Control a scaler card and its integration time.

    The scaler card is configured with an integration time and can be
    triggered to start a counting period. The counting period is complete
    when the start-count signal returns to ``False``.
    """

    def __init__(
        self, prefix: str, start_count_suffix: str, count_suffix: str, name: str = ""
    ):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.integration_time = epics_signal_rw(float, prefix + count_suffix)

        self.start_count = epics_signal_rw(bool, prefix + start_count_suffix)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """Set the scaler integration time."""
        await self.integration_time.set(value)

    @AsyncStatus.wrap
    async def trigger(self):
        """Start a scaler count and wait for it to complete."""
        await self.start_count.set(True)
        await wait_for_value(self.start_count, False, None)


T = TypeVar("T", bound=Device)


class ScalerCardChannels(StandardReadable, Triggerable, Movable[float], Generic[T]):
    """Expose the channels of a scaler card as a readable device.

    The channels are read from the supplied device and the scaler card
    controller is used to configure and trigger the acquisition. Calling
    :meth:`set` sets the scaler integration time, while :meth:`trigger`
    starts a count and waits for it to complete.
    """

    def __init__(self, channels: T, controller: ScalerCardController, name: str = ""):
        with self.add_children_as_readables():
            self.channel = channels

        controller.add_readables([channels])

        self.controller_ref = Reference(controller)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """Set the scaler integration time."""
        await self.controller_ref().set(value)

    @AsyncStatus.wrap
    async def trigger(self):
        """Start a scaler count and wait for it to complete."""
        await self.controller_ref().trigger()
