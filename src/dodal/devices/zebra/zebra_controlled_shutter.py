from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    DeviceMock,
    SignalRW,
    StandardReadable,
    StrictEnum,
    YesNo,
    callback_on_mock_put,
    default_mock_class,
    derived_signal_rw,
    set_and_wait_for_other_value,
    set_mock_value,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w

from dodal.devices.fast_shutter import GenericFastShutter, OpenClose


class ZebraShutterState(StrictEnum):
    CLOSE = "Close"
    OPEN = "Open"


class ZebraShutterControl(StrictEnum):
    MANUAL = "Manual"
    AUTO = "Auto"


class MXZebraShutter(StandardReadable, Movable[ZebraShutterState]):
    """The shutter on most MX beamlines is controlled by the zebra.

    Internally in the zebra there are two AND gates, one for manual control and one for
    automatic control. A soft input (aliased to control_mode) will switch between
    which of these AND gates to use. For the manual gate the shutter is then controlled
    by a different soft input (aliased to manual_position_setpoint). Both these AND
    gates then feed into an OR gate, which then feeds to the shutter.
    """

    def __init__(self, prefix: str, name: str = ""):
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


class MockZebraFastShutter(DeviceMock["ZebraFastShutter"]):
    async def connect(self, device: "ZebraFastShutter") -> None:
        callback_on_mock_put(
            device._set_pv,  # noqa: SLF001
            lambda state, *_, **__: set_mock_value(
                device._get_pv,  # noqa: SLF001
                1 if state == YesNo.YES else 0,
            ),
        )


@default_mock_class(MockZebraFastShutter)
class ZebraFastShutter(GenericFastShutter[OpenClose]):
    """A fast shutter controlled by the zebra that doesn't have the automatic/manual
    protection on top that the MXZebraShutter does. See https://jira.diamond.ac.uk/browse/I15_1-1626
    to bring them in line.
    """

    def __init__(
        self,
        set_pv: str,
        get_pv: str,
        name: str = "",
    ):
        self._set_pv = epics_signal_w(YesNo, set_pv)
        self._get_pv = epics_signal_r(int, get_pv)
        super().__init__(OpenClose.OPEN, OpenClose.CLOSE, name)

    def _create_shutter_state(self) -> SignalRW[OpenClose]:
        return derived_signal_rw(
            self._read_shutter_state,
            self._set_shutter_state,
            get_pv=self._get_pv,
        )

    def _read_shutter_state(self, get_pv: int) -> OpenClose:
        return OpenClose.CLOSE if get_pv == 0 else OpenClose.OPEN

    async def _set_shutter_state(self, value: OpenClose):
        set_value = YesNo.YES if value == OpenClose.OPEN else YesNo.NO
        readback_value = 1 if value == OpenClose.OPEN else 0
        await set_and_wait_for_other_value(
            self._set_pv, set_value, self._get_pv, readback_value
        )
