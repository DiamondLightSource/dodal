from ophyd import Component
from ophyd.signal import InternalSignal

from dodal.devices.eiger import EigerDetector
from dodal.devices.eiger_odin import EigerFan, EigerOdin


class VMXMEigerFan(EigerFan):
    dev_shm_enable = Component(InternalSignal, "DevShmCache")


class VMXMEigerOdin(EigerOdin):
    fan = Component(VMXMEigerFan, "OD:FAN:")


class VMXMEiger(EigerDetector):
    odin = Component(VMXMEigerOdin)
