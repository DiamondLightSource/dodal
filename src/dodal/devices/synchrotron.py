from enum import Enum

from ophyd import Component, Device, EpicsSignal
from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_r


class PV(str, Enum):
    STATUS_PREFIX = "CS-CS-MSTAT-01:"
    TOP_UP_PREFIX = "SR-CS-FILL-01:"
    SIGNAL_PREFIX = "SR-DI-DCCT-01:"
    SIGNAL = "SIGNAL"
    MODE = "MODE"
    USRCNTDN = "USERCOUNTDN"
    BEAM_ENERGY = "BEAMENERGY"
    CNTDN = "COUNTDOWN"
    ENDCNTDN = "ENDCOUNTDN"


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
    synchrotron_mode = Component(EpicsSignal, PV.MODE, string=True)
    user_countdown = Component(EpicsSignal, PV.USRCNTDN)
    beam_energy = Component(EpicsSignal, PV.BEAM_ENERGY)


class SynchrotronTopUp(Device):
    start_countdown = Component(EpicsSignal, PV.CNTDN)
    end_countdown = Component(EpicsSignal, PV.ENDCNTDN)


class Synchrotron(Device):
    machine_status = Component(SynchrotronMachineStatus, PV.STATUS_PREFIX)
    top_up = Component(SynchrotronTopUp, PV.TOP_UP_PREFIX)
    ring_current = Component(EpicsSignal, PV.SIGNAL_PREFIX + PV.SIGNAL)


class OASynchrotron(StandardReadable):
    def __init__(self, prefix: str = PV.SIGNAL_PREFIX, name: str = "synchrotron"):
        self.ring_current = epics_signal_r(float, prefix + PV.SIGNAL)
        self.synchrotron_mode = epics_signal_r(
            SynchrotronMode, PV.STATUS_PREFIX + PV.MODE
        )
        self.machine_user_countdown = epics_signal_r(
            float, PV.STATUS_PREFIX + PV.USRCNTDN
        )
        self.beam_energy = epics_signal_r(float, PV.STATUS_PREFIX + PV.BEAM_ENERGY)
        self.topup_start_countdown = epics_signal_r(float, PV.TOP_UP_PREFIX + PV.CNTDN)
        self.top_up_end_countdown = epics_signal_r(
            float, PV.TOP_UP_PREFIX + PV.ENDCNTDN
        )

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
