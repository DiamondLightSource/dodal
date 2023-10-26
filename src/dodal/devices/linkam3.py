import asyncio
import logging
import time
from enum import Enum
from typing import Callable, List, Optional

from bluesky.protocols import Location
from ophyd_async.core import AsyncStatus, StandardReadable, observe_value
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw

logger = logging.getLogger("linkam3")
logger.setLevel(logging.INFO)


class PumpControl(Enum):
    Manual = "Manual"
    Auto = "Auto"


class Linkam3(StandardReadable):
    tolerance: float = 0.1
    """
    The deadband around the setpoint within which the position is assumed to
    have been reached
    """

    settle_time: int = 10
    """The delay between reaching the setpoint and the move being considered complete"""

    def __init__(self, prefix: str, name: str = ""):
        self.temp = epics_signal_r(float, prefix + ":TEMP")
        self.dsc = epics_signal_r(float, prefix + ":DSC")
        self.start_heat = epics_signal_rw(bool, prefix + ":STARTHEAT")

        self.ramp_rate = epics_signal_rw(
            float, prefix + ":RAMPRATE", prefix + ":RAMPRATE:SET"
        )
        self.ramp_time = epics_signal_r(float, prefix + ":RAMPTIME")
        self.set_point = epics_signal_rw(
            float, prefix + ":SETPOINT", prefix + ":SETPOINT:SET"
        )
        self.pump_control = epics_signal_r(
            PumpControl,
            prefix + ":LNP_MODE:SET",
        )
        self.speed = epics_signal_rw(
            float, prefix + ":LNP_SPEED", prefix + ":LNP_SPEED:SET"
        )

        self.chamber_vac = epics_signal_r(float, prefix + ":VAC_CHAMBER")
        self.sensor_vac = epics_signal_r(float, prefix + ":VAC_DATA1")

        self.error = epics_signal_r(str, prefix + ":CTRLLR:ERR")

        # status is a bitfield stored in a double?
        self.status = epics_signal_r(float, prefix + ":STATUS")

        self.set_readable_signals(
            read=(self.temp,), config=(self.ramp_rate, self.speed, self.set_point)
        )

        super().__init__(name=name)

    async def _move(self, new_position: float, watchers: List[Callable] = []):
        logger.info("Moving to %f", new_position)
        # time.monotonic won't go backwards in case of NTP corrections
        start = time.monotonic()
        old_position = await self.set_point.get_value()
        await self.set_point.set(new_position, wait=True)
        async for current_position in observe_value(self.temp):
            logger.info("Currently %f", current_position)
            for watcher in watchers:
                watcher(
                    name=self.name,
                    current=current_position,
                    initial=old_position,
                    target=new_position,
                    time_elapsed=time.monotonic() - start,
                )
            if abs(current_position - new_position) < self.tolerance:
                logger.info("At set point")
                await asyncio.sleep(self.settle_time)
                break

    def set(self, new_position: float, timeout: Optional[float] = None) -> AsyncStatus:
        watchers: List[Callable] = []
        coro = asyncio.wait_for(self._move(new_position, watchers), timeout=timeout)
        return AsyncStatus(coro, watchers)

    # TODO: Check bitshift order
    async def in_error(self) -> bool:
        return bool(int(await self.status.get_value()) & 1)

    async def at_setpoint(self) -> bool:
        return bool(int(await self.status.get_value()) & 1 << 1)

    async def heater_on(self) -> bool:
        return bool(int(await self.status.get_value()) & 1 << 2)

    async def pump_on(self) -> bool:
        return bool(int(await self.status.get_value()) & 1 << 3)

    async def pump_auto(self) -> bool:
        return bool(int(await self.status.get_value()) & 1 << 4)

    async def locate(self) -> Location:
        return {
            "readback": await self.temp.get_value(),
            "setpoint": await self.set_point.get_value(),
        }
