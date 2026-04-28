from abc import ABC, abstractmethod
from math import isclose

from ophyd_async.core import (
    EnumTypes,
    SignalR,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    derived_signal_r,
)
from ophyd_async.epics.core import epics_signal_r

PSS_SAFE_FOR_OPERATIONS = 0  # Hutch is locked and can't be entered
PLC_SAFE_FOR_OPERATIONS = 65535  # All 16 bits are True

PSS_SHUTTER_SUFFIX = "-PS-IOC-01:M14:LOP"
EXP_SHUTTER_1_INFIX = "-PS-SHTR-01"


class PLCInterlockState(StrictEnum):
    FAILED = "Failed"
    RUN_ILKS_OK = "Run Ilks Ok"
    OK = "OK"
    DISARMED = "Disarmed"


class BaseInterlock(ABC, StandardReadable):
    status: SignalR[float | EnumTypes]
    bl_prefix: str

    def __init__(
        self,
        signal_type: type[EnumTypes] | type[float],
        bl_prefix: str,
        interlock_infix: str,
        interlock_suffix: str,
        name: str = "",
    ) -> None:
        pv_address = f"{bl_prefix}{interlock_infix}{interlock_suffix}"

        with self.add_children_as_readables():
            self.status = epics_signal_r(signal_type, pv_address)

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.is_safe = derived_signal_r(
                self._safe_to_operate,
                status=self.status,
            )
        super().__init__(name)

    @abstractmethod
    def _safe_to_operate(self, status: float | EnumTypes) -> bool:
        """Abstract method to define if interlock allows shutter to operate."""


class PSSInterlock(BaseInterlock):
    """Device to check the interlock status of the hutch using PSS pv."""

    def __init__(
        self,
        bl_prefix: str,
        shtr_infix: str = "",
        interlock_suffix: str = PSS_SHUTTER_SUFFIX,
        name: str = "",
    ) -> None:
        super().__init__(
            signal_type=float,
            bl_prefix=bl_prefix,
            interlock_infix=shtr_infix,
            interlock_suffix=interlock_suffix,
            name=name,
        )

    def _safe_to_operate(self, status: float | EnumTypes) -> bool:
        """If the status value is 0, hutch has been searched and locked and it is safe \
        to operate the shutter.
        If the status value is not 0 (usually set to 7), the hutch is open and the \
        shutter should not be in use.
        """
        return isclose(float(status), PSS_SAFE_FOR_OPERATIONS, abs_tol=5e-2)


class IntPLCInterlock(BaseInterlock):
    """Device to check the interlock state using integer PLC pv."""

    def __init__(
        self,
        bl_prefix: str,
        shtr_infix: str = "",
        interlock_suffix: str = "",
        name: str = "",
    ) -> None:
        super().__init__(
            signal_type=int,
            bl_prefix=bl_prefix,
            interlock_infix=shtr_infix,
            interlock_suffix=interlock_suffix,
            name=name,
        )

    def _safe_to_operate(self, status: float | EnumTypes) -> bool:
        """Check device is safe to operate.

        If the status value is not 65535 (healhty), the interlock has been tripped and
        the device cannot be operated.
        """
        return isclose(float(status), PLC_SAFE_FOR_OPERATIONS, abs_tol=5e-2)


class EnumPLCInterlock(BaseInterlock):
    """Device to check the interlock state using Enum PLC pv."""

    def __init__(
        self,
        bl_prefix: str,
        shtr_infix: str = "",
        interlock_suffix: str = EXP_SHUTTER_1_INFIX,
        name: str = "",
    ) -> None:
        super().__init__(
            signal_type=PLCInterlockState,
            bl_prefix=bl_prefix,
            interlock_infix=shtr_infix,
            interlock_suffix=interlock_suffix,
            name=name,
        )

    def _safe_to_operate(self, status: float | EnumTypes) -> bool:
        """If the status value is OK or Run Ilk OK, shutter is open or safe to operate.

        If the status value is "OK", valve or shutter is open and interlocks are OK to
        operate. If the status value is "Run Ilks Ok", the opening action can be
        started. If the status value is not OK ("Failed" or "Disarmed"), interlocks have
        failed and the shutter cannot be operated. Disarmed status applies only to fast
        shutters.
        """
        return (status == PLCInterlockState.OK) | (
            status == PLCInterlockState.RUN_ILKS_OK
        )
