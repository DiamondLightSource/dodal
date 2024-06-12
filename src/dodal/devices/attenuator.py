import asyncio
import string

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    DeviceVector,
    SignalR,
    StandardReadable,
    wait_for_value,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw, epics_signal_x

from dodal.log import LOGGER


class Attenuator(StandardReadable, Movable):
    """The attenuator will insert filters into the beam to reduce its transmission.

    This device should be set with:
        yield from bps.set(attenuator, desired_transmission)

    Where desired_transmission is fraction e.g. 0-1. When the actual_transmission is
    read from the device it is also fractional"""

    def __init__(self, prefix: str, name: str = ""):
        self._calculated_filter_states: DeviceVector[SignalR[int]] = DeviceVector(
            {
                int(digit, 16): epics_signal_r(int, f"{prefix}DEC_TO_BIN.B{digit}")
                for digit in string.hexdigits
                if not digit.islower()
            }
        )
        self._filters_in_position: DeviceVector[SignalR[bool]] = DeviceVector(
            {
                i - 1: epics_signal_r(bool, f"{prefix}FILTER{i}:INLIM")
                for i in range(1, 17)
            }
        )

        self._desired_transmission = epics_signal_rw(float, prefix + "T2A:SETVAL1")
        self._use_current_energy = epics_signal_x(prefix + "E2WL:USECURRENTENERGY.PROC")
        self._change = epics_signal_x(prefix + "FANOUT")

        with self.add_children_as_readables():
            self.actual_transmission = epics_signal_r(float, prefix + "MATCH")

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, transmission: float):
        """Set the transmission to the fractional (0-1) value given.

        The attenuator IOC will then insert filters to reach the desired transmission for
        the current beamline energy, the set will only complete when they have all been
        applied.
        """

        LOGGER.debug("Using current energy ")
        await self._use_current_energy.trigger()
        LOGGER.info(f"Setting desired transmission to {transmission}")
        await self._desired_transmission.set(transmission)
        LOGGER.debug("Sending change filter command")
        await self._change.trigger()

        await asyncio.gather(
            *[
                wait_for_value(
                    self._filters_in_position[i],
                    await self._calculated_filter_states[i].get_value(),
                    None,
                )
                for i in range(16)
            ]
        )
