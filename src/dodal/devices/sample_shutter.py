from enum import Enum
from typing import Union

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO

from dodal.devices.status import await_value


class OpenState(Enum):
    CLOSE = 0
    OPEN = 1


class SampleShutter(Device):
    """Simple device to trigger the pneumatic in/out"""

    pos: EpicsSignal = Component(EpicsSignal, "CTRL2")
    pos_rbv: EpicsSignalRO = Component(EpicsSignalRO, "STA")

    def set(self, open_val: Union[int, OpenState]):
        if isinstance(open_val, OpenState):
            open_val = open_val.value
        sp_status = self.pos.set(open_val)
        rbv_status = await_value(self.pos_rbv, open_val)
        return sp_status & rbv_status
