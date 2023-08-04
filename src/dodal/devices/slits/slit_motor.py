from ophyd import Device
from bluesky.protocols import Movable

class SlitMotor(Device, Movable):
    pass