from ophyd_async.core import Device
from ophyd_async.epics.motion import Motor


class XYZPositioner(Device):
    def __init__(self, prefix: str, name: str):
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")
        super().__init__(name)
