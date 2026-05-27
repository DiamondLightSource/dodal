import asyncio

from bluesky.protocols import Reading, Triggerable
from ophyd_async.core import (
    AsyncStatus,
    DeviceMock,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    default_mock_class,
    set_and_wait_for_value,
    set_mock_value,
)
from ophyd_async.epics.core import epics_signal_rw, wait_for_good_state


class MockScalerController(DeviceMock["ScalerController"]):
    async def connect(self, device: "ScalerController"):
        set_mock_value(device.counting, False)

        async def _complete():
            await asyncio.sleep(0.2)
            set_mock_value(device.counting, False)

        def _on_value(value: dict[str, Reading[bool]]):
            if value[device.counting.name]["value"] is True:
                asyncio.create_task(_complete())

        # Can't use callback_on_mock_put as this is called before the mock put, we need
        # to simulate after mock put update.
        device.counting.subscribe_reading(_on_value)


@default_mock_class(MockScalerController)
class ScalerController(StandardReadable, Triggerable):
    """Scaler controller that is triggerable. It will set the counting signal to True
    and then waits for it to be False.
    """

    def __init__(self, prefix: str, name: str = ""):
        self.counting = epics_signal_rw(bool, prefix + ".CNT")
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.count_period = epics_signal_rw(float, prefix + ".TP")

        self._acquire_status: AsyncStatus | None = None
        # Store the prefix so that the SimpleChannelScaler can reuse.
        self.prefix = prefix

        super().__init__(name)

    @AsyncStatus.wrap
    async def trigger(self):
        print("before set_and_wait")

        self._acquire_status = await set_and_wait_for_value(
            self.counting, True, wait_for_set_completion=True
        )

        print("after set_and_wait")

        await self._acquire_status

        print("after acquire status")

        await wait_for_good_state(self.counting, {False})

        print("after wait_for_good_state")


class SimpleChannelScaler(StandardReadable, Triggerable):
    """Create individual channel for a scaler. A ScalerController is used for the
    Trigger logic. It will also add this instance signals as readables to the
    ScannableController and also add the controllers count_period signal to this
    classes read configuration.
    """

    def __init__(
        self,
        scalar_controller: ScalerController,
        channel: int,
        name: str = "",
    ):
        self._scaler_controller_ref = Reference(scalar_controller)

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.count = epics_signal_rw(
                float, f"{scalar_controller.prefix}.S{channel}"
            )

        super().__init__(name)

        scalar_controller.add_readables([self])
        # Avoid circular read configuration by specifying individual signal
        self.add_readables(
            [scalar_controller.count_period], StandardReadableFormat.CONFIG_SIGNAL
        )

    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.count.set(value)

    @AsyncStatus.wrap
    async def trigger(self):
        await self._scaler_controller_ref().trigger()
