import asyncio
import time

from bluesky.protocols import Location
from ophyd_async.core import (
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    WatchableAsyncStatus,
    WatcherUpdate,
    observe_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class PumpControl(StrictEnum):
    MANUAL = "Manual"
    AUTO = "Auto"


class Linkam3(StandardReadable):
    """Device to represent a Linkam3 temperature controller

    Attributes:
        tolerance (float): Deadband around the setpoint within which the position is assumed to have been reached
        settle_time (int): The delay between reaching the setpoint and the move being considered complete

    Args:
        prefix (str): PV prefix for this device
        name (str): unique name for this device
    """

    tolerance: float = 0.5
    settle_time: int = 0

    def __init__(self, prefix: str, name: str = ""):
        self.temp = epics_signal_r(float, prefix + "TEMP:")
        self.dsc = epics_signal_r(float, prefix + "DSC:")
        self.start_heat = epics_signal_rw(bool, prefix + "STARTHEAT:")

        self.ramp_rate = epics_signal_rw(
            float, prefix + "RAMPRATE:", prefix + "RAMPRATE:SET:"
        )
        self.ramp_time = epics_signal_r(float, prefix + "RAMPTIME:")
        self.set_point = epics_signal_rw(
            float, prefix + "SETPOINT:", prefix + "SETPOINT:SET:"
        )
        self.pump_control = epics_signal_r(
            PumpControl,
            prefix + "LNP_MODE:SET:",
        )
        self.speed = epics_signal_rw(
            float, prefix + "LNP_SPEED:", prefix + "LNP_SPEED:SET:"
        )

        self.chamber_vac = epics_signal_r(float, prefix + "VAC_CHAMBER:")
        self.sensor_vac = epics_signal_r(float, prefix + "VAC_DATA1:")

        self.error = epics_signal_r(str, prefix + "CTRLLR:ERR:")

        # status is a bitfield stored in a double?
        self.status = epics_signal_r(float, prefix + "STATUS:")

        self.add_readables((self.temp,), format=StandardReadableFormat.HINTED_SIGNAL)
        self.add_readables(
            (self.ramp_rate, self.speed, self.set_point),
            format=StandardReadableFormat.CONFIG_SIGNAL,
        )

        super().__init__(name=name)

    @WatchableAsyncStatus.wrap
    async def set(self, new_position: float, timeout: float | None = None):
        # time.monotonic won't go backwards in case of NTP corrections
        start = time.monotonic()
        old_position = await self.set_point.get_value()
        await self.set_point.set(new_position, wait=True)
        async for current_position in observe_value(self.temp):
            yield WatcherUpdate(
                name=self.name,
                current=current_position,
                initial=old_position,
                target=new_position,
                time_elapsed=time.monotonic() - start,
            )
            if abs(current_position - new_position) < self.tolerance:
                await asyncio.sleep(self.settle_time)
                break

    # TODO: Make use of values in Status.
    # https://github.com/DiamondLightSource/dodal/issues/338
    async def _is_nth_bit_set(self, n: int) -> bool:
        return bool(int(await self.status.get_value()) & 1 << n)

    async def in_error(self) -> bool:
        return await self._is_nth_bit_set(0)

    async def at_setpoint(self) -> bool:
        return await self._is_nth_bit_set(1)

    async def heater_on(self) -> bool:
        return await self._is_nth_bit_set(2)

    async def pump_on(self) -> bool:
        return await self._is_nth_bit_set(3)

    async def pump_auto(self) -> bool:
        return await self._is_nth_bit_set(4)

    async def locate(self) -> Location:
        return {
            "readback": await self.temp.get_value(),
            "setpoint": await self.set_point.get_value(),
        }
