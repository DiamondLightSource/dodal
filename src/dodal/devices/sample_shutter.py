from enum import Enum

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO

from dodal.devices.status import await_value


class OpenState(Enum):
    CLOSE = 0
    OPEN = 1


class SampleShutter(Device):
    """Simple device to trigger the pneumatic in/out"""

    pos: EpicsSignal = Component(EpicsSignal, "CTRL2")
    pos_rbv: EpicsSignalRO = Component(EpicsSignalRO, "STA")

    def set(self, open: int):
        sp_status = self.pos.set(open)
        rbv_status = await_value(self.pos_rbv, open)
        return sp_status & rbv_status
