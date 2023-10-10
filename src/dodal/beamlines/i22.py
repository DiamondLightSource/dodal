from ..parameters.gda_directory_provider import GDADirectoryProvider
from ophyd_async.epics.areadetector import HDFStatsPilatus
from ophyd_async.panda import PandA
from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw



class Linkam(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.setpoint = epics_signal_rw(float, prefix + "RAMP:LIMIT:SET")
        self.readback = epics_signal_r(float, prefix + "TEMP")
        self.ramp_rate = epics_signal_rw(float, prefix + "RAMP:RATE:SET")
        self.set_readable_signals(config=[self.ramp_rate], read=[self.readback])
        super().__init__(name)

    def set_name(self, name: str):
        super().set_name(name)
        # Readback should be named the same as its parent in read()
        self.readback.set_name(name)


def saxs(directory_provider: GDADirectoryProvider):
    return HDFStatsPilatus("BL22I-EA-DET-01:", directory_provider)

def saxs(directory_provider: GDADirectoryProvider):
    return HDFStatsPilatus("BL22I-EA-DET-01:", directory_provider)

def panda(**kwargs):
    return PandA("BL22I-MO-PANDA-01:")

def linkam(**kwargs):
    return Linkam("BL22I-EA-TEMPC-01:")
