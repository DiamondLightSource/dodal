import asyncio
import string

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    DeviceVector,
    SignalR,
    StandardReadable,
    StrictEnum,
    SubsetEnum,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_x

from dodal.devices.attenuator.filter import FilterMotor
from dodal.log import LOGGER

DEFAULT_TIMEOUT = 60


class ReadOnlyAttenuator(StandardReadable):
    """A read-only attenuator class with a minimum set of PVs for reading.

    The actual_transmission will return a fractional transmission between 0-1.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            # Closest obtainable transmission to the current desired transmission given the specific
            # set of filters in the attenuator. This value updates immediately after setting desired
            # transmission, before the motors may have finished moving. It is not a readback value.
            self.actual_transmission = epics_signal_r(float, prefix + "MATCH")

        super().__init__(name)


class BinaryFilterAttenuator(ReadOnlyAttenuator, Movable[float]):
    """The attenuator will insert filters into the beam to reduce its transmission.
    In this attenuator, each filter can be in one of two states: IN or OUT

    This device should be set with:
        yield from bps.set(attenuator, desired_transmission)

    Where desired_transmission is fraction e.g. 0-1. When the actual_transmission is
    read from the device it is also fractional"""

    def __init__(self, prefix: str, num_filters: int, name: str = ""):
        self._calculated_filter_states: DeviceVector[SignalR[int]] = DeviceVector(
            {
                int(digit, num_filters): epics_signal_r(
                    int, f"{prefix}DEC_TO_BIN.B{digit}"
                )
                for digit in string.hexdigits
                if not digit.islower()
            }
        )
        self._filters_in_position: DeviceVector[SignalR[bool]] = DeviceVector(
            {
                i - 1: epics_signal_r(bool, f"{prefix}FILTER{i}:INLIM")
                for i in range(1, num_filters + 1)
            }
        )

        self._desired_transmission = epics_signal_rw(float, prefix + "T2A:SETVAL1")
        self._use_current_energy = epics_signal_x(prefix + "E2WL:USECURRENTENERGY.PROC")
        self._change = epics_signal_x(prefix + "FANOUT")

        super().__init__(prefix, name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """Set the transmission to the fractional (0-1) value given.

        The attenuator IOC will then insert filters to reach the desired transmission for
        the current beamline energy, the set will only complete when they have all been
        applied.
        """

        LOGGER.debug("Using current energy ")
        await self._use_current_energy.trigger()
        LOGGER.info(f"Setting desired transmission to {value}")
        await self._desired_transmission.set(value)
        LOGGER.debug("Sending change filter command")
        await self._change.trigger()

        await asyncio.gather(
            *[
                wait_for_value(
                    self._filters_in_position[i],
                    bool(await self._calculated_filter_states[i].get_value()),
                    DEFAULT_TIMEOUT,
                )
                for i in range(16)
            ]
        )


# Replace with ophyd async enum after https://github.com/bluesky/ophyd-async/pull/1067
class YesNo(StrictEnum):
    YES = "YES"
    NO = "NO"


# Time given to allow for motors to begin moving after the desired transmission has been set,
# so that we can work out when the set is complete.
ENUM_ATTENUATOR_SETTLE_TIME_S = 0.15


class EnumFilterAttenuator(ReadOnlyAttenuator, Movable[float]):
    """The attenuator will insert filters into the beam to reduce its transmission.

    This device is currently working, but feature incomplete. See https://github.com/DiamondLightSource/dodal/issues/972

    In this attenuator, the state of a filter corresponds to the selected material,
    e.g Ag50, in contrast to being either 'IN' or 'OUT'; see BinaryFilterAttenuator.
    """

    def __init__(
        self,
        prefix: str,
        filter_selection: tuple[type[SubsetEnum], ...],
        name: str = "",
    ):
        self._auto_move_on_desired_transmission_set = epics_signal_rw(
            YesNo, prefix + "AUTOMOVE"
        )
        self._desired_transmission = epics_signal_rw(float, prefix + "T2A:SETVAL1")
        self._use_current_energy = epics_signal_x(prefix + "E2WL:USECURRENTENERGY.PROC")

        with self.add_children_as_readables():
            self._filters: DeviceVector[FilterMotor] = DeviceVector(
                {
                    index: FilterMotor(f"{prefix}MP{index + 1}:", filter, name)
                    for index, filter in enumerate(filter_selection)
                }
            )
        super().__init__(prefix, name=name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """Set the transmission to the fractional (0-1) value given.

        The attenuator IOC will then insert filters to reach the desired transmission for
        the current beamline energy, the set will only complete when they have all been
        applied.
        """

        # auto move should normally be on, but check here incase it was manually turned off
        await self._auto_move_on_desired_transmission_set.set(YesNo.YES)

        # Currently uncertain if _use_current_energy correctly waits for completion: https://github.com/DiamondLightSource/dodal/issues/1588
        await self._use_current_energy.trigger()
        await self._desired_transmission.set(value)

        # Give EPICS a chance to start moving the filter motors. Not needed after
        # a transmission readback PV is added at the controls level: https://jira.diamond.ac.uk/browse/I24-725
        await asyncio.sleep(ENUM_ATTENUATOR_SETTLE_TIME_S)
        coros = [
            wait_for_value(self._filters[i].done_move, 1, timeout=DEFAULT_TIMEOUT)
            for i in self._filters
        ]
        await asyncio.gather(*coros)
