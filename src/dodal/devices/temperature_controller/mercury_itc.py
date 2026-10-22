from ophyd_async.core import StandardReadable, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class MercuryITC(StandardReadable):
    """Device for controlling and reading from a MercuryITC temperature controller.

    Args:
        prefix (str): The EPICS prefix for the Mercury device.
        name (str, optional): Name for the device.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.user_setpoint = epics_signal_rw(
                float, f"{prefix}READ_TEMP_LOOP_TSET", f"{prefix}SET_TEMP_LOOP_TSET"
            )
            self.heater_output = epics_signal_rw(
                float, f"{prefix}READ_TEMP_LOOP_HSET", f"{prefix}SET_TEMP_LOOP_HSET"
            )

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.readback = epics_signal_r(float, read_pv=f"{prefix}READ_TEMP_SIG_TEMP")

        super().__init__(name=name)
