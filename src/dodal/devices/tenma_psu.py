from ophyd_async.core import StandardReadable, StandardReadableFormat, derived_signal_rw
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w


class TenmaPSU(StandardReadable):
    """A device representing a Tenma power supply unit (PSU)."""

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        self._output_rbv = epics_signal_r(bool, f"{prefix}STATUS_RBV.B6")
        self._output_on = epics_signal_w(bool, f"{prefix}OUTPUT_ON.PROC")
        self._output_off = epics_signal_w(bool, f"{prefix}OUTPUT_OFF.PROC")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.voltage_sp = epics_signal_rw(
                float, f"{prefix}SET_VOLTAGE:RBV", f"{prefix}SET_VOLTAGE"
            )
            self.current_sp = epics_signal_rw(
                float, f"{prefix}SET_CURRENT:RBV", f"{prefix}SET_CURRENT"
            )

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.voltage_readback = epics_signal_r(float, f"{prefix}VOLTAGE")
            self.current_readback = epics_signal_r(float, f"{prefix}CURRENT")
            self.power_readback = epics_signal_r(float, f"{prefix}POWER")

            self.output = derived_signal_rw(
                self._derived_output,
                self._set_output,
                rbv=self._output_rbv,
            )

        super().__init__(name=name)

    def _derived_output(self, rbv: bool) -> bool:
        return rbv

    async def _set_output(self, value: bool):
        if value:
            await self._output_on.set(True)
        else:
            await self._output_off.set(True)
