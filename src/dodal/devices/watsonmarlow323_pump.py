from ophyd_async.core import StandardReadable, StandardReadableFormat, StrictEnum
from ophyd_async.epics.core import epics_signal_rw


class WatsonMarlow323PumpEnable(StrictEnum):
    DISABLED = "Disabled"
    ENABLED = "Enabled"


class WatsonMarlow323PumpDirection(StrictEnum):
    CLOCKWISE = "CW"
    COUNTER_CLOCKWISE = "CCW"


class WatsonMarlow323PumpState(StrictEnum):
    STOPPED = "STOP"
    STARTED = "START"


class WatsonMarlow323Pump(StandardReadable):
    """Watson Marlow 323 Peristaltic Pump device"""

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.direction = epics_signal_rw(
                WatsonMarlow323PumpDirection,
                read_pv=prefix + "INFO:DIR",
                write_pv=prefix + "SET:DIR",
            )
            self.state = epics_signal_rw(
                WatsonMarlow323PumpState,
                read_pv=prefix + "INFO:RUN",
                write_pv=prefix + "SET:RUN",
            )
            self.speed = epics_signal_rw(
                float, read_pv=prefix + "INFO:SPD", write_pv=prefix + "SET:SPD"
            )

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.enabled = epics_signal_rw(
                WatsonMarlow323PumpEnable,
                prefix + "DISABLE",
            )

        super().__init__(name=name)
