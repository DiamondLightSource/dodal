import asyncio

from bluesky.protocols import Movable, Triggerable
from ophyd_async.core import (
    AsyncStatus,
    DeviceMock,
    StandardReadable,
    StandardReadableFormat,
    default_mock_class,
    set_and_wait_for_value,
    set_mock_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, wait_for_good_state


class MockScalerController(DeviceMock["ScalerController"]):
    async def _complete(self):
        await asyncio.sleep(0.01)
        set_mock_value(self._counting, False)

    def _on_value(self, value):
        if value[self._counting.name]["value"]:
            asyncio.create_task(self._complete())

    async def connect(self, device):
        self._counting = device.counting

        set_mock_value(device.counting, False)
        # Can't use callback_on_mock_put as this is called before the mock put, we need
        # to simulate after mock put update. subscribe_reading listeners are stored in
        # a set, so repeatedly subscribing this bound method is harmless and does not
        # create duplicate callbacks.
        device.counting.subscribe_reading(self._on_value)


@default_mock_class(MockScalerController)
class ScalerController(
    StandardReadable,
    Triggerable,
    Movable,
):
    """Scaler controller that is triggerable. It will set the counting signal to True
    and then waits for it to be False.
    """

    def __init__(self, prefix: str, name: str = ""):
        self.counting = epics_signal_rw(bool, prefix + ".CNT")
        with self.add_children_as_readables():
            # Readings of count for specific channels
            self.hm3amp20 = epics_signal_r(float, prefix + f".S{2}")
            self.sm5amp8 = epics_signal_r(float, prefix + f".S{3}")
            self.smpmamp39 = epics_signal_r(float, prefix + f".S{4}")
            self.rfdamp10 = epics_signal_r(float, prefix + f".S{5}")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.count_time = epics_signal_rw(float, prefix + ".TP")

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.count_time.set(value)

    @AsyncStatus.wrap
    async def trigger(self):
        await set_and_wait_for_value(self.counting, True, wait_for_set_completion=True)
        await wait_for_good_state(self.counting, {False})
