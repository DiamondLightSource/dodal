from ophyd_async.core import (
    FlyMotorInfo,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    SubsetEnum,
    WatchableAsyncStatus,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w


class HighFieldMangetSweepTypes(StrictEnum):
    FAST = "Fast"
    SLOW = "Slow"


class HighFieldMagnetStatus(SubsetEnum):
    HOLD = "Hold"
    TO_SETPOINT = "To Setpoint"
    TO_ZERO = "To Zero"
    CLAMP = "Clamp"


class HighFieldMagnetStatusRBV(SubsetEnum):
    HOLD = "Hold"
    TO_SETPOINT = "To Setpoint"
    TO_ZERO = "To Zero"
    CLAMPED = "Clamped"


class HighFieldMagnet(
    StandardReadable,
    # Locatable[float],
    # Stoppable,
    # Flyable,
    # Preparable,
    # Subscribable[float],
):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.sweeprate = epics_signal_rw(
                float,
                read_pv=prefix + "RBV:FIELDSWEEPRATE",
                write_pv=prefix + "SET:FIELDSWEEPRATE",
            )
            self.sweep_type = epics_signal_rw(
                HighFieldMangetSweepTypes,
                read_pv=prefix + "STS:SWEEPMODE:TYPE",
                write_pv=prefix + "SET:SWEEPMODE:TYPE",
            )
            self.set_move_readback = epics_signal_r(
                HighFieldMagnetStatusRBV,
                read_pv=prefix + "STS:ACTIVITY",
            )
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.user_readback = epics_signal_r(float, prefix + "RBV:DEMANDFIELD")

        self.set_move = epics_signal_w(
            HighFieldMagnetStatus,
            write_pv=prefix + "SET:ACTIVITY",
        )
        self.user_setpoint = epics_signal_rw(
            float,
            read_pv=prefix + "RBV:SETPOINTFIELD",
            write_pv=prefix + "SET:SETPOINTFIELD",
        )

        self._set_success = True

        self._fly_info: FlyMotorInfo | None = None

        self._fly_status: WatchableAsyncStatus | None = None

        super().__init__(name=name)

    def set_name(self, name: str, *, child_name_separator: str | None = None) -> None:
        super().set_name(name, child_name_separator=child_name_separator)
        # Readback should be named the same as its parent in read()
        self.user_readback.set_name(name)
