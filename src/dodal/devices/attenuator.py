import asyncio
import string

from ophyd_async.core import (
    AsyncStatus,
    DeviceVector,
    SignalR,
    StandardReadable,
    wait_for_value,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw, epics_signal_x

from dodal.log import LOGGER


class Attenuator(StandardReadable):
    """The attenuator will ...

    Any reference to transmission (both read and write) in this Device is fraction
    e.g. 0-1"""

    def __init__(self, prefix: str, name: str = ""):
        self.calculated_filter_states: DeviceVector[SignalR[bool]] = DeviceVector(
            {
                int(digit, 16): epics_signal_r(int, f"{prefix}DEC_TO_BIN.B{digit}")
                for digit in string.hexdigits
                if digit.isupper()
            }
        )
        self.filters_in_position: DeviceVector[SignalR[bool]] = DeviceVector(
            {i: epics_signal_r(bool, f"{prefix}FILTER{i}:INLIM") for i in range(1, 17)}
        )

        self.desired_transmission = epics_signal_rw(float, prefix + "T2A:SETVAL1")
        self.use_current_energy = epics_signal_x(prefix + "E2WL:USECURRENTENERGY.PROC")
        self.change = epics_signal_x(prefix + "FANOUT")

        with self.add_children_as_readables():
            self.actual_transmission = epics_signal_r(float, prefix + "MATCH")

    @AsyncStatus.wrap
    async def set(self, transmission: float):
        """Set the transmission to the fractional value given.
        Args:
            transmission (float): A fraction to set transmission to between 0-1
        Get desired states and calculated states, return a status which is complete once they are equal
        """

        LOGGER.info("Using current energy ")
        await self.use_current_energy.trigger()
        LOGGER.info(f"Setting desired transmission to {transmission}")
        await self.desired_transmission.set(transmission)
        LOGGER.info("Sending change filter command")
        await self.change.trigger()

        await asyncio.gather(
            *[
                wait_for_value(
                    self.filters_in_position[i],
                    await self.calculated_filter_states[i].get_value(),
                    None,
                )
                for i in range(16)
            ]
        )
