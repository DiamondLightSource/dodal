from enum import Enum

from ophyd import Component, Device, EpicsSignal


class SynchrotronMode(Enum):
    SHUTDOWN = "Shutdown"
    INJECTION = "Injection"
    NOBEAM = "No Beam"
    DEV = "Mach. Dev."
    USER = "User"
    SPECIAL = "Special"
    STARTUP = "BL Startup"
    UNKNOWN = "Unknown"


class SynchrotoronMachineStatus(Device):
    synchrotron_mode = Component(EpicsSignal, "MODE", string=True)
    user_countdown = Component(EpicsSignal, "USERCOUNTDN")
    beam_energy = Component(EpicsSignal, "BEAMENERGY")


class SynchrotronTopUp(Device):
    start_countdown = Component(EpicsSignal, "COUNTDOWN")
    end_countdown = Component(EpicsSignal, "ENDCOUNTDN")


class Synchrotron(Device):
    machine_status = Component(SynchrotoronMachineStatus, "CS-CS-MSTAT-01:")
    top_up = Component(SynchrotronTopUp, "SR-CS-FILL-01:")

    ring_current = Component(EpicsSignal, "SR-DI-DCCT-01:SIGNAL")
