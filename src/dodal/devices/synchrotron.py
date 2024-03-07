from enum import Enum

from ophyd import Component, Device, EpicsSignal
from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_r

_STATUS_PREFIX = "CS-CS-MSTAT-01:"
_TOP_UP_PREFIX = "SR-CS-FILL-01:"
_SIGNAL_PREFIX = "SR-DI-DCCT-01:"
_SIGNAL = "SIGNAL"
_MODE = "MODE"
_USRCNTDN = "USERCOUNTDN"
_BEAM_ENERGY = "BEAMENERGY"
_CNTDN = "COUNTDOWN"
_ENDCNTDN = "ENDCOUNTDN"


class SynchrotronMode(str, Enum):
    SHUTDOWN = "Shutdown"
    INJECTION = "Injection"
    NOBEAM = "No Beam"
    DEV = "Mach. Dev."
    USER = "User"
    SPECIAL = "Special"
    STARTUP = "BL Startup"
    UNKNOWN = "Unknown"


class SynchrotronMachineStatus(Device):
    synchrotron_mode = Component(EpicsSignal, _MODE, string=True)
    user_countdown = Component(EpicsSignal, _USRCNTDN)
    beam_energy = Component(EpicsSignal, _BEAM_ENERGY)


class SynchrotronTopUp(Device):
    start_countdown = Component(EpicsSignal, _CNTDN)
    end_countdown = Component(EpicsSignal, _ENDCNTDN)


class Synchrotron(Device):
    machine_status = Component(SynchrotronMachineStatus, _STATUS_PREFIX)
    top_up = Component(SynchrotronTopUp, _TOP_UP_PREFIX)
    ring_current = Component(EpicsSignal, _SIGNAL_PREFIX + _SIGNAL)


class OASynchrotron(StandardReadable):
    def __init__(self, prefix: str = _SIGNAL_PREFIX, name: str = "synchrotron"):
        self.ring_current = epics_signal_r(float, prefix + _SIGNAL)
        self.synchrotron_mode = epics_signal_r(SynchrotronMode, _STATUS_PREFIX + _MODE)
        self.machine_user_countdown = epics_signal_r(float, _STATUS_PREFIX + _USRCNTDN)
        self.beam_energy = epics_signal_r(float, _STATUS_PREFIX + _BEAM_ENERGY)
        self.topup_start_countdown = epics_signal_r(float, _TOP_UP_PREFIX + _CNTDN)
        self.top_up_end_countdown = epics_signal_r(float, _TOP_UP_PREFIX + _ENDCNTDN)

        self.set_readable_signals(
            read=[
                self.ring_current,
                self.machine_user_countdown,
                self.topup_start_countdown,
                self.top_up_end_countdown,
            ],
            config=[
                self.beam_energy,
                self.synchrotron_mode,
            ],
        )
        super().__init__(name=name)
