import asyncio

from bluesky.protocols import Reading
from ophyd_async.core import DeviceMock, SignalDatatype, set_mock_value


def reset_signal_on_update_mock_factory(
    signal_name: str,
    trigger_value: SignalDatatype,
    reset_value: SignalDatatype,
    reset_delay: float = 0.01,
):
    """Create a device mock that resets a signal following a reading update.

    The mock subscribes to reading updates on a specified signal. When the
    signal reading matches the trigger value, the mock waits for the
    configured delay before setting the signal to its reset value.

    This is useful for simulating asynchronous hardware behaviour, such as
    automatically returning a state PV to its idle value after an acquisition
    completes. It allows devices using set-and-wait logic to complete
    successfully when connected in mock mode.

    Args:
        signal_name: Name of the device signal to monitor.
        trigger_value: Reading value that causes the signal to be reset.
        reset_value: Value to set after the matching reading update.
        reset_delay: Delay in seconds between observing the matching reading
            and setting the reset value.

    Returns:
        A DeviceMock subclass implementing the reading-update behaviour.
    """

    class ReadingUpdateResetMock(DeviceMock):
        """Mock that automatically updates a signal following a reading."""

        def _on_value(self, value: dict[str, Reading[SignalDatatype]]):
            """Schedule a signal reset when the trigger value is observed."""

            async def _complete():
                await asyncio.sleep(reset_delay)
                set_mock_value(self._mock_trigger_signal, reset_value)

            if value[self._mock_trigger_signal.name]["value"] == trigger_value:
                asyncio.create_task(_complete())

        async def connect(self, device: DeviceMock):
            """Connect the mock to the device signal and initialise its value."""
            signal = getattr(device, signal_name)
            self._mock_trigger_signal = signal

            set_mock_value(signal, reset_value)
            # Can't use callback_on_mock_put as this is called before the mock put, we
            # need to simulate after mock put update. subscribe_reading listeners are
            # stored in a set, so repeatedly subscribing this bound method is harmless
            # and does not create duplicate callbacks.
            signal.subscribe_reading(self._on_value)

    return ReadingUpdateResetMock
