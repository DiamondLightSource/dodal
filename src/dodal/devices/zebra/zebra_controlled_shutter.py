from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    StandardReadable,
    StrictEnum,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w


class ZebraShutterState(StrictEnum):
    CLOSE = "Close"
    OPEN = "Open"


class ZebraShutterControl(StrictEnum):
    MANUAL = "Manual"
    AUTO = "Auto"


class ZebraShutter(StandardReadable, Movable[ZebraShutterState]):
    """The shutter on most MX beamlines is controlled by the zebra.

    Internally in the zebra there are two AND gates, one for manual control and one for
    automatic control. A soft input (aliased to control_mode) will switch between
    which of these AND gates to use. For the manual gate the shutter is then controlled
    by a different soft input (aliased to manual_position_setpoint). Both these AND
    gates then feed into an OR gate, which then feeds to the shutter."""

    def __init__(self, prefix: str, name: str):
        self._manual_position_setpoint = epics_signal_w(
            ZebraShutterState, prefix + "CTRL2"
        )
        self.control_mode = epics_signal_rw(ZebraShutterControl, prefix + "CTRL1")

        with self.add_children_as_readables():
            self.position_readback = epics_signal_r(ZebraShutterState, prefix + "STA")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: ZebraShutterState):
        if await self.control_mode.get_value() == ZebraShutterControl.AUTO:
            raise UserWarning(
                f"Tried to set shutter to {value.value} but the shutter is in auto mode."
            )
        await self._manual_position_setpoint.set(value)
        return await wait_for_value(
            signal=self.position_readback,
            match=value,
            timeout=DEFAULT_TIMEOUT,
        )
