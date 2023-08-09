from ophyd import Device, Component
from bluesky.protocols import Movable

from .slit_motor import SlitMotor


class S5_BL02J_AL_SLITS_95(Device, Movable):
    """Slit simulator set up as BL02J temporary equipment.
    
    Many thanks to Andrew Foster!"""
    y_real: Device = Component(SlitMotor, "Y:PLUS")

    def set(self, value):
        return self.y_real.set(value)

