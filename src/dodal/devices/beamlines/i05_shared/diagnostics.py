import asyncio
from typing import Self

from bluesky.protocols import Movable, Triggerable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    Settings,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    derived_signal_rw,
    soft_signal_rw,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.common.enums import EnabledDisabledUpper
from dodal.devices.current_amplifiers import (
    CurrentAmp,
)


class ADCMode(StrictEnum):
    CONTINUOUS = "CONTINUOUS"
    TRIGGERED = "TRIGGERED"
    GATED = "GATED"


class ADCFrequency(StrictEnum):
    HZ200 = "200Hz"
    HZ100 = "100Hz"
    HZ50 = "50Hz"
    HZ40 = "40Hz"
    HZ25 = "25Hz"
    HZ20 = "20Hz"
    HZ10 = "10Hz"
    HZ5 = "5Hz"
    HZ4 = "4Hz"
    HZ2 = "2Hz"
    HZ1 = "1Hz"


class ADCAcquire(StrictEnum):
    DONE = "Done"
    ACQUIRE = "Acquire"


# class DiagnosticDet(StandardReadable):
#     def __init__(
#         self,
#         prefix: str,
#         amplifier: CurrentAmp,
#         amp_suffix: str = "GAIN",
#         name: str = "",
#     ) -> None:
#         with self.add_children_as_readables():
#             self.amplifier = self.amplifier

#         with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
#             self.drain_current = epics_signal_r(float, prefix + "I")

#         with self.add_children_as_readables():
#             self.average = epics_signal_r(float, prefix + "IAV")

#         with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
#             self.mode = epics_signal_rw(ADCMode, prefix + "IAV:ADC1_MODE")
#             self.enable = epics_signal_rw(
#                 EnabledDisabledUpper, prefix + "IAV:ADC1_ENABLED"
#             )
#             self.retrigger = epics_signal_rw(
#                 EnabledDisabledUpper, prefix + "IAV:ADC1_RETRIGGER"
#             )
#             self.frequency = epics_signal_rw(ADCFrequency, prefix + "IAV:FREQ1")

#             self.soft_trigger = epics_signal_rw(ADCAcquire, prefix + "IAV:ADC1_TRIGGER")

#         super().__init__(name)


class BekhoffADC(StandardReadable, Triggerable, Movable[float]):
    """Bekhoff Analog-to-Digital Converter control and readback."""

    def __init__(
        self,
        prefix: str,
        current_prefix: str = "VALUE",
        sampling_rate: int = 1000,
        name: str = "",
    ):
        self.value = epics_signal_r(int, prefix + current_prefix)

        # with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
        #     self.current = derived_signal_r(
        #         self._voltage_to_current,
        #         derived_units="A",
        #         voltage=self.value,
        #         gain=amplifier.gain_readback,
        #     )

        with self.add_children_as_readables():
            self.state = epics_signal_r(str, prefix + "STATE")
            self.integral = epics_signal_r(float, prefix + "INTEGRAL")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.mode = epics_signal_rw(ADCMode, prefix + "MODE")
            self.enable = epics_signal_rw(EnabledDisabledUpper, prefix + "ENABLED")
            self.retrigger = epics_signal_rw(EnabledDisabledUpper, prefix + "RETRIGGER")
            self.samples = epics_signal_rw(int, prefix + "SAMPLES")
            self.average = epics_signal_rw(int, prefix + "AVERAGE")
            self.soft_trigger = epics_signal_rw(ADCAcquire, prefix + "TRIGGER")
            self.sampling_rate = soft_signal_rw(int, sampling_rate)
            self.collection_time = derived_signal_rw(
                self._samples_to_collection_time,
                self._set_collection_time,
                derived_units="s",
                samples=self.samples,
                sampling_rate=self.sampling_rate,
            )
            # This needs to be standardised with controls
            # self.frequency = epics_signal_rw(ADCFrequency, prefix + "IAV:FREQ1")

        self._original_settings: Settings[Self] | None = None

        super().__init__(name)

    def _voltage_to_current(self, voltage: float, gain: float) -> float:
        return voltage / gain

    def _samples_to_collection_time(self, samples: int, sampling_rate: int) -> float:
        return samples / sampling_rate

    async def _set_collection_time(self, collection_time: float) -> None:
        sampling_rate = await self.sampling_rate.get_value()
        samples = max(1, round(collection_time * sampling_rate))
        await asyncio.gather(self.samples.set(samples), self.average.set(samples))

    @AsyncStatus.wrap
    async def stage(self):
        """Configure ADC for software triggering, caching original settings so can
        restored after data collection.
        """
        mode, enable, retrigger, samples, average = await asyncio.gather(
            self.mode.get_value(),
            self.enable.get_value(),
            self.retrigger.get_value(),
            self.samples.get_value(),
            self.average.get_value(),
        )
        self._original_settings = Settings(self)
        self._original_settings[self.mode] = mode
        self._original_settings[self.enable] = enable
        self._original_settings[self.retrigger] = retrigger
        self._original_settings[self.samples] = samples
        self._original_settings[self.average] = average

        await asyncio.gather(
            self.mode.set(ADCMode.TRIGGERED),
            self.enable.set(EnabledDisabledUpper.ENABLED),
            self.retrigger.set(EnabledDisabledUpper.ENABLED),
        )

    @AsyncStatus.wrap
    async def set(self, value: float):
        """Set the collection time."""
        await self.collection_time.set(value)

    @AsyncStatus.wrap
    async def trigger(self):
        """Trigger ADC acquisition and wait for completion."""
        time = await self.collection_time.get_value()
        await self.soft_trigger.set(ADCAcquire.ACQUIRE)
        await wait_for_value(self.state, ADCAcquire.DONE, time + DEFAULT_TIMEOUT)

    @AsyncStatus.wrap
    async def unstage(self):
        """Restore original ADC configuration to values before data collection."""
        if self._original_settings is None:
            return
        signal_tasks = [
            signal.set(value) for signal, value in self._original_settings.items()
        ]
        await asyncio.gather(*signal_tasks)
        self._original_settings = None


class DiagnosticDet(StandardReadable):
    def __init__(
        self,
        prefix: str,
        amplifier: CurrentAmp,
        amp_suffix: str = "GAIN",
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.amplifier = amplifier
            self.adc = BekhoffADC(prefix, name="adc")

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.drain_current = epics_signal_r(float, prefix + "I")

        with self.add_children_as_readables():
            self.average = epics_signal_r(float, prefix + "IAV")

        super().__init__(name)
