from asyncio import gather
from enum import Enum
from typing import Dict

from bluesky.protocols import Descriptor, Reading
from ophyd import Component, Device, EpicsSignal
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.core import Device as OADevice
from ophyd_async.core.utils import merge_gathered_dicts
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
_UNITS = ".EGU"
_PRECISION = ".PREC"


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


class OASynchrotronTopUp(StandardReadable):
    def __init__(self, prefix: str = _TOP_UP_PREFIX, name: str = "topup"):
        self.start_countdown = epics_signal_r(float, prefix + _CNTDN)
        self.start_countdown_units = epics_signal_r(str, prefix + _CNTDN + _UNITS)
        self.start_countdown_precision = epics_signal_r(
            int, prefix + _CNTDN + _PRECISION
        )
        self.end_countdown = epics_signal_r(float, prefix + _ENDCNTDN)
        self.end_countdown_units = epics_signal_r(str, prefix + _ENDCNTDN + _UNITS)
        self.end_countdown_precision = epics_signal_r(
            int, prefix + _ENDCNTDN + _PRECISION
        )

        self.set_readable_signals(
            read=[
                self.start_countdown,
            ],
            config=[self.start_countdown_units, self.start_countdown_precision],
        )
        super().__init__(name=name)


class OASynchrotronMachineStatus(StandardReadable):
    def __init__(self, prefix: str = _STATUS_PREFIX, name: str = "machine status"):
        self.synchrotron_mode = epics_signal_r(SynchrotronMode, prefix + _MODE)
        self.user_countdown = epics_signal_r(float, prefix + _USRCNTDN)
        self.user_countdown_units = epics_signal_r(str, prefix + _USRCNTDN + _UNITS)
        self.user_countdown_precision = epics_signal_r(
            int, prefix + _USRCNTDN + _PRECISION
        )
        self.beam_energy = epics_signal_r(float, prefix + _BEAM_ENERGY)
        self.units = epics_signal_r(str, prefix + _BEAM_ENERGY + _UNITS)
        self.precision = epics_signal_r(int, prefix + _BEAM_ENERGY + _PRECISION)

        self.set_readable_signals(
            read=[
                self.beam_energy,
            ],
            config=[self.synchrotron_mode, self.units, self.precision],
        )
        super().__init__(name=name)


class OASynchrotronRingCurrent(StandardReadable):
    def __init__(self, prefix: str = _SIGNAL_PREFIX, name: str = "ring current"):
        self.current = epics_signal_r(float, prefix + _SIGNAL)
        self.units = epics_signal_r(str, prefix + _SIGNAL + _UNITS)
        self.precision = epics_signal_r(int, prefix + _SIGNAL + _PRECISION)

        self.set_readable_signals(
            read=[
                self.current,
            ],
            config=[self.units, self.precision],
        )
        super().__init__(name=name)


class OASynchrotron(OADevice):
    def __init__(self, prefix: str = _SIGNAL_PREFIX, name: str = "synchrotron"):
        self.machine_status = OASynchrotronMachineStatus()
        self.topup = OASynchrotronTopUp()
        self.ring_current = OASynchrotronRingCurrent()

        self.components = [self.ring_current, self.topup, self.machine_status]

        super().__init__(name=name)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await gather(*{device.stage().task for device in self.components})

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        await gather(*{device.unstage().task for device in self.components})

    async def describe_configuration(self) -> Dict[str, Descriptor]:
        return await merge_gathered_dicts(
            [device.describe_configuration() for device in self.components]
        )

    async def read_configuration(self) -> Dict[str, Reading]:
        return await merge_gathered_dicts(
            [device.read_configuration() for device in self.components]
        )

    async def describe(self) -> Dict[str, Descriptor]:
        return await merge_gathered_dicts(
            [device.describe() for device in self.components]
        )

    async def read(self) -> Dict[str, Reading]:
        return await merge_gathered_dicts([device.read() for device in self.components])
