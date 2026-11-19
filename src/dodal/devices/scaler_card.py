from collections.abc import MutableMapping
from typing import Generic, TypeVar

from bluesky.protocols import Movable, Triggerable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    Device,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    default_mock_class,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.util.mock_behaviour import reset_signal_on_update_mock_factory


@default_mock_class(reset_signal_on_update_mock_factory("start_count", True, False))
class ScalerCardController(StandardReadable, Triggerable, Movable[float]):
    """Control a scaler card and its readable channels.

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
        timeout = await self.integration_time.get_value() + DEFAULT_TIMEOUT
        await wait_for_value(self.start_count, False, timeout)


DeviceT = TypeVar("DeviceT", bound=Device)


class ScalerCard(StandardReadable, Triggerable, Movable[float], Generic[DeviceT]):
    """Expose a logical group of channels from a scaler card.

    The channels are exposed as a readable device and are associated with a
    :class:`ScalerCardController` that controls the underlying scaler card. Multiple
    instances of this class can share the same controller, allowing different groups of
    scaler channels to be exposed as separate logical devices while being acquired by
    the same physical scaler card. The channels are also added as readables with the
    controller, so the controller exposes all channels associated with the scaler card.
    This allows the controller to represent the complete set of scaler channels, while
    each  :class:`ScalerCard` instance provides access to only its associated
    group. Calling :meth:`set` sets the scaler integration time via the controller,
    while :meth:`trigger` starts the controller count and waits for it to complete.
    """

    def __init__(
        self, channels: DeviceT, controller: ScalerCardController, name: str = ""
    ):
        with self.add_children_as_readables():
            self.channel = channels

        # ophyd-async DeviceVector/DeviceMap case
        if isinstance(channels, MutableMapping):
            controller.add_readables(list(channels.values()))
        else:
            controller.add_readables([channels])

        self.add_readables(
            [controller.integration_time], StandardReadableFormat.CONFIG_SIGNAL
        )
        self.controller_ref = Reference(controller)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """Set the scaler integration time on the controller."""
        await self.controller_ref().set(value)

    @AsyncStatus.wrap
    async def trigger(self):
        """Start a scaler count on the controller and wait for it to complete."""
        await self.controller_ref().trigger()
